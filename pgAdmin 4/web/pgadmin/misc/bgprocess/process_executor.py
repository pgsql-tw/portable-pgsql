# -*- coding: utf-8 -*-

##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2020, The pgAdmin Development Team
# This software is released under the PostgreSQL License
#
##########################################################################

"""
This python script is responsible for executing a process, and logs its output,
and error in the given output directory.

We will create a detached process, which executes this script.

This script will:
* Fetch the configuration from the given database.
* Run the given executable specified in the configuration with the arguments.
* Create log files for both stdout, and stdout.
* Update the start time, end time, exit code, etc in the configuration
  database.

Args:
  list of program and arguments passed to it.

It also depends on the following environment variable for proper execution.
PROCID - Process-id
OUTDIR - Output directory
"""
from __future__ import print_function

# To make print function compatible with python2 & python3
import sys
import os
from datetime import datetime, timedelta, tzinfo
from subprocess import Popen, PIPE
from threading import Thread
import signal

_IS_WIN = (os.name == 'nt')
_IS_PY2 = (sys.version_info[0] == 2)
_ZERO = timedelta(0)
_sys_encoding = None
_fs_encoding = None
_u = None
_out_dir = None
_log_file = None

if _IS_PY2:
    def _log(msg):
        with open(_log_file, 'a') as fp:
            fp.write(('INFO:: %s\n' % str(msg)))
else:
    def _log(msg):
        with open(_log_file, 'a') as fp:
            fp.write(
                ('INFO:: %s\n' % msg.encode('ascii', 'xmlcharrefreplace'))
            )


def unescape_dquotes_process_arg(arg):
    # Double quotes has special meaning for shell command line and they are
    # run without the double quotes.
    #
    # Remove the saviour #DQ#

    # This cannot be at common place as this file executes
    # separately from pgadmin
    dq_id = "#DQ#"

    if arg.startswith(dq_id) and arg.endswith(dq_id):
        return '{0}'.format(arg[len(dq_id):-len(dq_id)])
    else:
        return arg


def _log_exception():
    type_, value_, traceback_ = info = sys.exc_info()

    with open(_log_file, 'a') as fp:
        from traceback import format_exception
        res = ''.join(
            format_exception(type_, value_, traceback_)
        )

        fp.write('EXCEPTION::\n{0}'.format(res))
        return res


# Copied the 'UTC' class from the 'pytz' package to allow to run this script
# without any external dependent library, and can be used with any python
# version.
class UTC(tzinfo):
    """UTC

    Optimized UTC implementation. It unpickles using the single module global
    instance defined beneath this class declaration.
    """
    zone = "UTC"

    _utcoffset = _ZERO
    _dst = _ZERO
    _tzname = zone

    def fromutc(self, dt):
        if dt.tzinfo is None:
            return self.localize(dt)
        return super(UTC.__class__, self).fromutc(dt)

    def utcoffset(self, dt):
        return _ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return _ZERO

    def localize(self, dt, is_dst=False):
        '''Convert naive time to local time'''
        if dt.tzinfo is not None:
            raise ValueError('Not naive datetime (tzinfo is already set)')
        return dt.replace(tzinfo=self)

    def normalize(self, dt, is_dst=False):
        '''Correct the timezone information on the given datetime'''
        if dt.tzinfo is self:
            return dt
        if dt.tzinfo is None:
            raise ValueError('Naive time - no tzinfo set')
        return dt.astimezone(self)

    def __repr__(self):
        return "<UTC>"

    def __str__(self):
        return "UTC"


def get_current_time(format='%Y-%m-%d %H:%M:%S.%f %z'):
    return datetime.utcnow().replace(
        tzinfo=UTC()
    ).strftime(format)


class ProcessLogger(Thread):
    """
    This class definition is responsible for capturing & logging
    stdout & stderr messages from subprocess

    Methods:
    --------
    * __init__(stream_type)
     - This method is use to initlize the ProcessLogger class object

    * log(msg)
     - Log message in the orderly manner.

    * run()
     - Reads the stdout/stderr for messages and sent them to logger
    """

    def __init__(self, stream_type):
        """
        This method is use to initialize the ProcessLogger class object

        Args:
            stream_type: Type of STD (std)

        Returns:
            None
        """
        import codecs

        Thread.__init__(self)
        self.process = None
        self.stream = None
        self.logger = open(os.path.join(_out_dir, stream_type), 'wb')

    def attach_process_stream(self, process, stream):
        """
        This function will attach a process and its stream with this thread.

        Args:
            process: Process
            stream: Stream attached with the process

        Returns:
            None
        """
        self.process = process
        self.stream = stream

    if not _IS_PY2:
        def log(self, msg):
            """
            This function will update log file

            Args:
                msg: message

            Returns:
                None
            """
            # Write into log file
            if self.logger:
                if msg:
                    self.logger.write(
                        get_current_time(
                            format='%y%m%d%H%M%S%f'
                        ).encode('utf-8')
                    )
                    self.logger.write(b',')
                    self.logger.write(
                        msg.lstrip(b'\r\n' if _IS_WIN else b'\n')
                    )
                    self.logger.write(os.linesep.encode('utf-8'))

                return True
            return False
    else:
        def log(self, msg):
            """
            This function will update log file

            Args:
                msg: message

            Returns:
                None
            """
            # Write into log file
            if self.logger:
                if msg:
                    self.logger.write(
                        b'{0},{1}{2}'.format(
                            get_current_time(
                                format='%y%m%d%H%M%S%f'
                            ),
                            msg.lstrip(
                                b'\r\n' if _IS_WIN else b'\n'
                            ),
                            os.linesep
                        )
                    )

                return True
            return False

    def run(self):
        if self.process and self.stream:
            while True:
                nextline = self.stream.readline()

                if nextline:
                    self.log(nextline)
                else:
                    if self.process.poll() is not None:
                        break

    def release(self):
        if self.logger:
            self.logger.close()
            self.logger = None


def update_status(**kw):
    """
    This function will updates process stats

    Args:
        kwargs - Process configuration details

    Returns:
        None
    """
    import json

    if _out_dir:
        status = dict(
            (k, v) for k, v in kw.items()
            if k in ('start_time', 'end_time', 'exit_code', 'pid')
        )
        _log('Updating the status:\n{0}'.format(json.dumps(status)))
        with open(os.path.join(_out_dir, 'status'), 'w') as fp:
            json.dump(status, fp)
    else:
        raise ValueError("Please verify pid and db_file arguments.")


def execute(argv):
    """
    This function will execute the background process

    Returns:
        None
    """
    command = argv[1:]
    args = dict()
    _log('Initialize the process execution: {0}'.format(command))

    # Create seprate thread for stdout and stderr
    process_stdout = ProcessLogger('out')
    process_stderr = ProcessLogger('err')
    process = None

    try:
        # update start_time
        args.update({
            'start_time': get_current_time(),
            'stdout': process_stdout.log,
            'stderr': process_stderr.log,
            'pid': os.getpid()
        })

        # Update start time
        update_status(**args)
        _log('Status updated...')

        if 'PROCID' in os.environ and os.environ['PROCID'] in os.environ:
            os.environ['PGPASSWORD'] = os.environ[os.environ['PROCID']]

        kwargs = dict()
        kwargs['close_fds'] = False
        kwargs['shell'] = True if _IS_WIN else False

        # We need environment variables & values in string
        if _IS_PY2:
            _log('Converting the environment variable in the bytes format...')
            kwargs['env'] = convert_environment_variables(os.environ.copy())
        else:
            kwargs['env'] = os.environ.copy()

        _log('Starting the command execution...')
        process = Popen(
            command, stdout=PIPE, stderr=PIPE, stdin=None, **kwargs
        )
        args.update({
            'start_time': get_current_time(),
            'stdout': process_stdout.log,
            'stderr': process_stderr.log,
            'pid': process.pid
        })
        update_status(**args)
        _log('Status updated after starting child process...')

        _log('Attaching the loggers to stdout, and stderr...')
        # Attach the stream to the process logger, and start logging.
        process_stdout.attach_process_stream(process, process.stdout)
        process_stdout.start()
        process_stderr.attach_process_stream(process, process.stderr)
        process_stderr.start()

        # Join both threads together
        process_stdout.join()
        process_stderr.join()

        _log('Waiting for the process to finish...')
        # Child process return code
        exitCode = process.wait()

        if exitCode is None:
            exitCode = process.poll()

        _log('Process exited with code: {0}'.format(exitCode))
        args.update({'exit_code': exitCode})

        # Add end_time
        args.update({'end_time': get_current_time()})

        # Fetch last output, and error from process if it has missed.
        data = process.communicate()
        if data:
            if data[0]:
                process_stdout.log(data[0])
            if data[1]:
                process_stderr.log(data[1])

    # If executable not found or invalid arguments passed
    except OSError as e:
        info = _log_exception()
        args.update({'exit_code': 500})
        if process_stderr:
            process_stderr.log(info)
        else:
            print("WARNING: ", e.strerror, file=sys.stderr)
        args.update({'end_time': get_current_time()})
        args.update({'exit_code': e.errno})

    # Unknown errors
    except Exception:
        info = _log_exception()
        args.update({'exit_code': 501})
        if process_stderr:
            process_stderr.log(info)
        else:
            print("WARNING: ", str(e), file=sys.stderr)
        args.update({'end_time': get_current_time()})
        args.update({'exit_code': -1})
    finally:
        # Update the execution end_time, and exit-code.
        update_status(**args)
        _log('Exiting the process executor...')
        if process_stderr:
            process_stderr.release()
        if process_stdout:
            process_stdout.release()
        _log('Bye!')


# Let's ignore all the signal comming to us.
def signal_handler(signal, msg):
    pass


def convert_environment_variables(env):
    """
    This function is use to convert environment variable to string
    because environment variable must be string in popen
    :param env: Dict of environment variable
    :return: Encoded environment variable as string
    """
    temp_env = dict()
    for key, value in env.items():
        try:
            if not isinstance(key, str):
                key = key.encode(_sys_encoding)
            if not isinstance(value, str):
                value = value.encode(_sys_encoding)
            temp_env[key] = value
        except Exception:
            _log_exception()
    return temp_env


if __name__ == '__main__':

    argv = [
        unescape_dquotes_process_arg(arg) for arg in sys.argv
    ]

    _sys_encoding = sys.getdefaultencoding()
    if not _sys_encoding or _sys_encoding == 'ascii':
        # Fall back to 'utf-8', if we couldn't determine the default encoding,
        # or 'ascii'.
        _sys_encoding = 'utf-8'

    _fs_encoding = sys.getfilesystemencoding()
    if not _fs_encoding or _fs_encoding == 'ascii':
        # Fall back to 'utf-8', if we couldn't determine the file-system
        # encoding or 'ascii'.
        _fs_encoding = 'utf-8'

    def u(_s, _encoding=_sys_encoding):
        if _IS_PY2:
            if isinstance(_s, str):
                return unicode(_s, _encoding)
        return _s
    _u = u

    _out_dir = u(os.environ['OUTDIR'])
    _log_file = os.path.join(_out_dir, ('log_%s' % os.getpid()))

    _log('Starting the process executor...')

    # Ignore any signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    _log('Disabled the SIGINT, SIGTERM signals...')

    if _IS_WIN:
        _log('Disable the SIGBREAKM signal (windows)...')
        signal.signal(signal.SIGBREAK, signal_handler)
        _log('Disabled the SIGBREAKM signal (windows)...')

        # For windows:
        # We would run the process_executor in the detached mode again to make
        # the child process to run as a daemon. And, it would run without
        # depending on the status of the web-server.
        if 'PGA_BGP_FOREGROUND' in os.environ and \
                os.environ['PGA_BGP_FOREGROUND'] == "1":
            _log('[CHILD] Start process execution...')
            # This is a child process running as the daemon process.
            # Let's do the job assigning to it.
            try:
                _log('Executing the command now from the detached child...')
                execute(argv)
            except Exception:
                _log_exception()
        else:
            from subprocess import CREATE_NEW_PROCESS_GROUP
            DETACHED_PROCESS = 0x00000008

            # Forward the standard input, output, and error stream to the
            # 'devnull'.
            stdin = open(os.devnull, "r")
            stdout = open(os.devnull, "a")
            stderr = open(os.devnull, "a")
            env = os.environ.copy()
            env['PGA_BGP_FOREGROUND'] = "1"

            # We need environment variables & values in string
            _log('[PARENT] Converting the environment variable in the '
                 'bytes format...')
            try:
                env = convert_environment_variables(env)
            except Exception:
                _log_exception()

            kwargs = {
                'stdin': stdin.fileno(),
                'stdout': stdout.fileno(),
                'stderr': stderr.fileno(),
                'creationflags': CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
                'close_fds': False,
                'cwd': _out_dir,
                'env': env
            }

            cmd = [sys.executable]
            cmd.extend(argv)

            _log('[PARENT] Command executings: {0}'.format(cmd))

            p = Popen(cmd, **kwargs)

            exitCode = p.poll()

            if exitCode is not None:
                _log(
                    '[PARENT] Child exited with exit-code#{0}...'.format(
                        exitCode
                    )
                )
            else:
                _log('[PARENT] Started the child with PID#{0}'.format(p.pid))

            # Question: Should we wait for sometime?
            # Answer: Looks the case...
            from time import sleep
            sleep(2)
            _log('[PARENT] Exiting...')
            sys.exit(0)
    else:
        r, w = os.pipe()

        # For POSIX:
        # We will fork the process, and run the child process as daemon, and
        # let it do the job.
        if os.fork() == 0:
            _log('[CHILD] Forked the child process...')
            # Hmm... So - I need to do the job now...
            try:
                os.close(r)

                _log('[CHILD] Make the child process leader...')
                # Let me be the process leader first.
                os.setsid()
                os.umask(0)

                _log('[CHILD] Make the child process leader...')
                w = os.fdopen(w, 'w')
                # Let me inform my parent - I will do the job, do not worry
                # now, and die peacefully.
                _log('[CHILD] Inform parent about successful child forking...')
                w.write('1')
                w.close()

                _log('[CHILD] Start executing the background process...')
                execute(argv)
            except Exception:
                _log_exception()
                sys.exit(1)
        else:
            os.close(w)
            r = os.fdopen(r)
            # I do not care, what the child send.
            r.read()
            _log('[PARENT] Got message from the child...')
            r.close()

            _log('[PARENT] Exiting...')
            sys.exit(0)
