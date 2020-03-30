##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2020, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

"""
Implementation of ServerManager
"""
import os
import datetime
import config
from flask import current_app, session
from flask_security import current_user
from flask_babelex import gettext

from pgadmin.utils import get_complete_file_path
from pgadmin.utils.crypto import decrypt
from pgadmin.utils.master_password import process_masterpass_disabled
from .connection import Connection
from pgadmin.model import Server, User
from pgadmin.utils.exception import ConnectionLost, SSHTunnelConnectionLost,\
    CryptKeyMissing
from pgadmin.utils.master_password import get_crypt_key

if config.SUPPORT_SSH_TUNNEL:
    from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError


class ServerManager(object):
    """
    class ServerManager

    This class contains the information about the given server.
    And, acts as connection manager for that particular session.
    """

    def __init__(self, server):
        self.connections = dict()
        self.local_bind_host = '127.0.0.1'
        self.local_bind_port = None
        self.tunnel_object = None
        self.tunnel_created = False

        self.update(server)

    def update(self, server):
        assert (server is not None)
        assert (isinstance(server, Server))

        self.ver = None
        self.sversion = None
        self.server_type = None
        self.server_cls = None
        self.password = None
        self.tunnel_password = None

        self.sid = server.id
        self.host = server.host
        self.hostaddr = server.hostaddr
        self.port = server.port
        self.db = server.maintenance_db
        self.did = None
        self.user = server.username
        self.password = server.password
        self.role = server.role
        self.ssl_mode = server.ssl_mode
        self.pinged = datetime.datetime.now()
        self.db_info = dict()
        self.server_types = None
        self.db_res = server.db_res
        self.passfile = server.passfile
        self.sslcert = server.sslcert
        self.sslkey = server.sslkey
        self.sslrootcert = server.sslrootcert
        self.sslcrl = server.sslcrl
        self.sslcompression = True if server.sslcompression else False
        self.service = server.service
        self.connect_timeout = \
            server.connect_timeout if server.connect_timeout else 0
        if config.SUPPORT_SSH_TUNNEL:
            self.use_ssh_tunnel = server.use_ssh_tunnel
            self.tunnel_host = server.tunnel_host
            self.tunnel_port = \
                22 if server.tunnel_port is None else server.tunnel_port
            self.tunnel_username = server.tunnel_username
            self.tunnel_authentication = 0 \
                if server.tunnel_authentication is None \
                else server.tunnel_authentication
            self.tunnel_identity_file = server.tunnel_identity_file
            self.tunnel_password = server.tunnel_password
        else:
            self.use_ssh_tunnel = 0
            self.tunnel_host = None
            self.tunnel_port = 22
            self.tunnel_username = None
            self.tunnel_authentication = None
            self.tunnel_identity_file = None
            self.tunnel_password = None

        for con in self.connections:
            self.connections[con]._release()

        self.update_session()

        self.connections = dict()

    def as_dict(self):
        """
        Returns a dictionary object representing the server manager.
        """
        if self.ver is None or len(self.connections) == 0:
            return None

        res = dict()
        res['sid'] = self.sid
        res['ver'] = self.ver
        res['sversion'] = self.sversion
        if hasattr(self, 'password') and self.password:
            # If running under PY2
            if hasattr(self.password, 'decode'):
                res['password'] = self.password.decode('utf-8')
            else:
                res['password'] = str(self.password)
        else:
            res['password'] = self.password

        if self.use_ssh_tunnel:
            if hasattr(self, 'tunnel_password') and self.tunnel_password:
                # If running under PY2
                if hasattr(self.tunnel_password, 'decode'):
                    res['tunnel_password'] = \
                        self.tunnel_password.decode('utf-8')
                else:
                    res['tunnel_password'] = str(self.tunnel_password)
            else:
                res['tunnel_password'] = self.tunnel_password

        connections = res['connections'] = dict()

        for conn_id in self.connections:
            conn = self.connections[conn_id].as_dict()

            if conn is not None:
                connections[conn_id] = conn

        return res

    def ServerVersion(self):
        return self.ver

    @property
    def version(self):
        return self.sversion

    def MajorVersion(self):
        if self.sversion is not None:
            return int(self.sversion / 10000)
        raise Exception("Information is not available.")

    def MinorVersion(self):
        if self.sversion:
            return int(int(self.sversion / 100) % 100)
        raise Exception("Information is not available.")

    def PatchVersion(self):
        if self.sversion:
            return int(int(self.sversion / 100) / 100)
        raise Exception("Information is not available.")

    def connection(
            self, database=None, conn_id=None, auto_reconnect=True, did=None,
            async_=None, use_binary_placeholder=False, array_to_string=False
    ):
        if database is not None:
            if hasattr(str, 'decode') and \
                    not isinstance(database, unicode):
                database = database.decode('utf-8')
            if did is not None:
                if did in self.db_info:
                    self.db_info[did]['datname'] = database
        else:
            if did is None:
                database = self.db
            elif did in self.db_info:
                database = self.db_info[did]['datname']
            else:
                maintenance_db_id = u'DB:{0}'.format(self.db)
                if maintenance_db_id in self.connections:
                    conn = self.connections[maintenance_db_id]
                    # try to connect maintenance db if not connected
                    if not conn.connected():
                        conn.connect()

                    if conn.connected():
                        status, res = conn.execute_dict(u"""
SELECT
    db.oid as did, db.datname, db.datallowconn,
    pg_encoding_to_char(db.encoding) AS serverencoding,
    has_database_privilege(db.oid, 'CREATE') as cancreate, datlastsysoid
FROM
    pg_database db
WHERE db.oid = {0}""".format(did))

                        if status and len(res['rows']) > 0:
                            for row in res['rows']:
                                self.db_info[did] = row
                                database = self.db_info[did]['datname']

                        if did not in self.db_info:
                            raise Exception(gettext(
                                "Could not find the specified database."
                            ))

        if not get_crypt_key()[0]:
            # the reason its not connected might be missing key
            raise CryptKeyMissing()

        if database is None:
            # Check SSH Tunnel is alive or not.
            if self.use_ssh_tunnel == 1:
                self.check_ssh_tunnel_alive()
            else:
                raise ConnectionLost(self.sid, None, None)

        my_id = (u'CONN:{0}'.format(conn_id)) if conn_id is not None else \
            (u'DB:{0}'.format(database))

        self.pinged = datetime.datetime.now()

        if my_id in self.connections:
            return self.connections[my_id]
        else:
            if async_ is None:
                async_ = 1 if conn_id is not None else 0
            else:
                async_ = 1 if async_ is True else 0
            self.connections[my_id] = Connection(
                self, my_id, database, auto_reconnect, async_,
                use_binary_placeholder=use_binary_placeholder,
                array_to_string=array_to_string
            )

            return self.connections[my_id]

    def _restore(self, data):
        """
        Helps restoring to reconnect the auto-connect connections smoothly on
        reload/restart of the app server..
        """
        # restore server version from flask session if flask server was
        # restarted. As we need server version to resolve sql template paths.
        masterpass_processed = process_masterpass_disabled()

        # The data variable is a copy so is not automatically synced
        # update here
        if masterpass_processed and 'password' in data:
            data['password'] = None
        if masterpass_processed and 'tunnel_password' in data:
            data['tunnel_password'] = None

        from pgadmin.browser.server_groups.servers.types import ServerType

        self.ver = data.get('ver', None)
        self.sversion = data.get('sversion', None)

        if self.ver and not self.server_type:
            for st in ServerType.types():
                if st.instanceOf(self.ver):
                    self.server_type = st.stype
                    self.server_cls = st
                    break

        # We need to know about the existing server variant supports during
        # first connection for identifications.
        self.pinged = datetime.datetime.now()
        try:
            if 'password' in data and data['password']:
                if hasattr(data['password'], 'encode'):
                    data['password'] = data['password'].encode('utf-8')
            if 'tunnel_password' in data and data['tunnel_password']:
                data['tunnel_password'] = \
                    data['tunnel_password'].encode('utf-8')
        except Exception as e:
            current_app.logger.exception(e)

        connections = data['connections']

        for conn_id in connections:
            conn_info = connections[conn_id]
            if conn_info['conn_id'] in self.connections:
                conn = self.connections[conn_info['conn_id']]
            else:
                conn = self.connections[conn_info['conn_id']] = Connection(
                    self, conn_info['conn_id'], conn_info['database'],
                    conn_info['auto_reconnect'], conn_info['async_'],
                    use_binary_placeholder=conn_info[
                        'use_binary_placeholder'],
                    array_to_string=conn_info['array_to_string']
                )

            # only try to reconnect if connection was connected previously
            # and auto_reconnect is true.
            if conn_info['wasConnected'] and conn_info['auto_reconnect']:
                try:
                    # Check SSH Tunnel needs to be created
                    if self.use_ssh_tunnel == 1 and \
                       not self.tunnel_created:
                        status, error = self.create_ssh_tunnel(
                            data['tunnel_password'])

                        # Check SSH Tunnel is alive or not.
                        self.check_ssh_tunnel_alive()

                    conn.connect(
                        password=data['password'],
                        server_types=ServerType.types()
                    )
                    # This will also update wasConnected flag in
                    # connection so no need to update the flag manually.
                except CryptKeyMissing:
                    # maintain the status as this will help to restore once
                    # the key is available
                    conn.wasConnected = conn_info['wasConnected']
                    conn.auto_reconnect = conn_info['auto_reconnect']
                except Exception as e:
                    current_app.logger.exception(e)
                    self.connections.pop(conn_info['conn_id'])
                    raise

    def _restore_connections(self):
        for conn_id in self.connections:
            conn = self.connections[conn_id]
            # only try to reconnect if connection was connected previously
            # and auto_reconnect is true.
            wasConnected = conn.wasConnected
            auto_reconnect = conn.auto_reconnect
            if conn.wasConnected and conn.auto_reconnect:
                try:
                    # Check SSH Tunnel needs to be created
                    if self.use_ssh_tunnel == 1 and \
                       not self.tunnel_created:
                        status, error = self.create_ssh_tunnel(
                            self.tunnel_password
                        )

                        # Check SSH Tunnel is alive or not.
                        self.check_ssh_tunnel_alive()

                    conn.connect()
                    # This will also update wasConnected flag in
                    # connection so no need to update the flag manually.
                except CryptKeyMissing:
                    # maintain the status as this will help to restore once
                    # the key is available
                    conn.wasConnected = wasConnected
                    conn.auto_reconnect = auto_reconnect
                except Exception as e:
                    self.connections.pop(conn_id)
                    current_app.logger.exception(e)
                    raise

    def release(self, database=None, conn_id=None, did=None):
        # Stop the SSH tunnel if release() function calls without
        # any parameter.
        if database is None and conn_id is None and did is None:
            self.stop_ssh_tunnel()

        if did is not None:
            if did in self.db_info and 'datname' in self.db_info[did]:
                database = self.db_info[did]['datname']
                if hasattr(str, 'decode') and \
                        not isinstance(database, unicode):
                    database = database.decode('utf-8')
                if database is None:
                    return False
            else:
                return False

        my_id = (u'CONN:{0}'.format(conn_id)) if conn_id is not None else \
            (u'DB:{0}'.format(database)) if database is not None else None

        if my_id is not None:
            if my_id in self.connections:
                self.connections[my_id]._release()
                del self.connections[my_id]
                if did is not None:
                    del self.db_info[did]

                if len(self.connections) == 0:
                    self.ver = None
                    self.sversion = None
                    self.server_type = None
                    self.server_cls = None
                    self.password = None

                self.update_session()

                return True
            else:
                return False

        for con_key in list(self.connections.keys()):
            conn = self.connections[con_key]
            # Cancel the ongoing transaction before closing the connection
            # as it may hang forever
            if conn.connected() and conn.conn_id is not None and \
               conn.conn_id.startswith('CONN:'):
                conn.cancel_transaction(conn.conn_id[5:])
            conn._release()

        self.connections = dict()
        self.ver = None
        self.sversion = None
        self.server_type = None
        self.server_cls = None
        self.password = None

        self.update_session()

        return True

    def _update_password(self, passwd):
        self.password = passwd
        for conn_id in self.connections:
            conn = self.connections[conn_id]
            if conn.conn is not None or conn.wasConnected is True:
                conn.password = passwd

    def update_session(self):
        managers = session['__pgsql_server_managers'] \
            if '__pgsql_server_managers' in session else dict()
        updated_mgr = self.as_dict()

        if not updated_mgr:
            if self.sid in managers:
                managers.pop(self.sid)
        else:
            managers[self.sid] = updated_mgr
        session['__pgsql_server_managers'] = managers
        session.force_write = True

    def utility(self, operation):
        """
        utility(operation)

        Returns: name of the utility which used for the operation
        """
        if self.server_cls is not None:
            return self.server_cls.utility(operation, self.sversion)

        return None

    def export_password_env(self, env):
        if self.password:
            crypt_key_present, crypt_key = get_crypt_key()
            if not crypt_key_present:
                return False, crypt_key

            password = decrypt(self.password, crypt_key).decode()
            os.environ[str(env)] = password

    def create_ssh_tunnel(self, tunnel_password):
        """
        This method is used to create ssh tunnel and update the IP Address and
        IP Address and port to localhost and the local bind port return by the
        SSHTunnelForwarder class.
        :return: True if tunnel is successfully created else error message.
        """
        # Fetch Logged in User Details.
        user = User.query.filter_by(id=current_user.id).first()
        if user is None:
            return False, gettext("Unauthorized request.")

        if tunnel_password is not None and tunnel_password != '':
            crypt_key_present, crypt_key = get_crypt_key()
            if not crypt_key_present:
                raise CryptKeyMissing()

            try:
                tunnel_password = decrypt(tunnel_password, crypt_key)
                # Handling of non ascii password (Python2)
                if hasattr(str, 'decode'):
                    tunnel_password = \
                        tunnel_password.decode('utf-8').encode('utf-8')
                # password is in bytes, for python3 we need it in string
                elif isinstance(tunnel_password, bytes):
                    tunnel_password = tunnel_password.decode()

            except Exception as e:
                current_app.logger.exception(e)
                return False, "Failed to decrypt the SSH tunnel " \
                              "password.\nError: {0}".format(str(e))

        try:
            # If authentication method is 1 then it uses identity file
            # and password
            if self.tunnel_authentication == 1:
                self.tunnel_object = SSHTunnelForwarder(
                    (self.tunnel_host, int(self.tunnel_port)),
                    ssh_username=self.tunnel_username,
                    ssh_pkey=get_complete_file_path(self.tunnel_identity_file),
                    ssh_private_key_password=tunnel_password,
                    remote_bind_address=(self.host, self.port)
                )
            else:
                self.tunnel_object = SSHTunnelForwarder(
                    (self.tunnel_host, int(self.tunnel_port)),
                    ssh_username=self.tunnel_username,
                    ssh_password=tunnel_password,
                    remote_bind_address=(self.host, self.port)
                )

            self.tunnel_object.start()
            self.tunnel_created = True
        except BaseSSHTunnelForwarderError as e:
            current_app.logger.exception(e)
            return False, "Failed to create the SSH tunnel." \
                          "\nError: {0}".format(str(e))

        # Update the port to communicate locally
        self.local_bind_port = self.tunnel_object.local_bind_port

        return True, None

    def check_ssh_tunnel_alive(self):
        # Check SSH Tunnel is alive or not. if it is not then
        # raise the ConnectionLost exception.
        if self.tunnel_object is None or not self.tunnel_object.is_active:
            self.tunnel_created = False
            raise SSHTunnelConnectionLost(self.tunnel_host)

    def stop_ssh_tunnel(self):
        # Stop the SSH tunnel if created.
        if self.tunnel_object and self.tunnel_object.is_active:
            self.tunnel_object.stop()
            self.local_bind_port = None
            self.tunnel_object = None
            self.tunnel_created = False
