##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2020, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

"""Implements View and Materialized View Node"""

import copy
from functools import wraps

import simplejson as json
from flask import render_template, request, jsonify, current_app
from flask_babelex import gettext

import pgadmin.browser.server_groups.servers.databases as databases
from config import PG_DEFAULT_DRIVER
from pgadmin.browser.server_groups.servers.databases.schemas.utils import \
    SchemaChildModule, parse_rule_definition, VacuumSettings, get_schema
from pgadmin.browser.server_groups.servers.utils import parse_priv_from_db, \
    parse_priv_to_db
from pgadmin.browser.utils import PGChildNodeView
from pgadmin.utils.ajax import make_json_response, internal_server_error, \
    make_response as ajax_response, gone
from pgadmin.utils.driver import get_driver
from pgadmin.tools.schema_diff.node_registry import SchemaDiffRegistry
from pgadmin.tools.schema_diff.compare import SchemaDiffObjectCompare


"""
    This module is responsible for generating two nodes
    1) View
    2) Materialized View

    We have created single file because view & material view has same
    functionality. It allows us to share the same submodules for both
    view, and material view modules.

    This modules uses separate template paths for each respective node
    - templates/view for View node
    - templates/materialized_view for the materialized view node

    [Each path contains node specific js files as well as sql template files.]
"""


class ViewModule(SchemaChildModule):
    """
    class ViewModule(SchemaChildModule):

        A module class for View node derived from SchemaChildModule.

    Methods:
    -------
    * __init__(*args, **kwargs)
      - Method is used to initialize the View and it's base module.

    * get_nodes(gid, sid, did, scid)
      - Method is used to generate the browser collection node.

    * node_inode()
      - Method is overridden from its base class to make the node as leaf node.

    * script_load()
      - Load the module script for View, when any of the server node is
        initialized.
    """
    NODE_TYPE = 'view'
    COLLECTION_LABEL = gettext("Views")

    def __init__(self, *args, **kwargs):
        """
        Method is used to initialize the ViewModule and it's base module.

        Args:
            *args:
            **kwargs:
        """
        super(ViewModule, self).__init__(*args, **kwargs)
        self.min_ver = None
        self.max_ver = None

    def get_nodes(self, gid, sid, did, scid):
        """
        Generate the collection node
        """
        yield self.generate_browser_collection_node(scid)

    @property
    def script_load(self):
        """
        Load the module script for views, when any database node is
        initialized, The reason is views are also listed under catalogs
        which are loaded under database node.
        """
        return databases.DatabaseModule.NODE_TYPE

    @property
    def csssnippets(self):
        """
        Returns a snippet of css to include in the page
        """
        snippets = [
            render_template(
                "browser/css/collection.css",
                node_type=self.node_type,
                _=gettext
            ),
            render_template(
                "views/css/view.css",
                node_type=self.node_type,
                _=gettext
            ),
            render_template(
                "mviews/css/mview.css",
                node_type='mview',
                _=gettext
            )
        ]

        for submodule in self.submodules:
            snippets.extend(submodule.csssnippets)

        return snippets


class MViewModule(ViewModule):
    """
     class MViewModule(ViewModule)
        A module class for the materialized view node derived from ViewModule.
    """

    NODE_TYPE = 'mview'
    COLLECTION_LABEL = gettext("Materialized Views")

    def __init__(self, *args, **kwargs):
        """
        Method is used to initialize the MViewModule and
        it's base module.

        Args:
            *args:
            **kwargs:
        """
        super(MViewModule, self).__init__(*args, **kwargs)
        self.min_ver = 90300
        self.max_ver = None
        self.min_gpdbver = 1000000000


view_blueprint = ViewModule(__name__)
mview_blueprint = MViewModule(__name__)


def check_precondition(f):
    """
    This function will behave as a decorator which will checks
    database connection before running view, it will also attaches
    manager,conn & template_path properties to instance of the method.

    Assumptions:
        This function will always be used as decorator of a class method.
    """

    @wraps(f)
    def wrap(*args, **kwargs):

        # Here args[0] will hold self & kwargs will hold gid,sid,did
        self = args[0]
        pg_driver = get_driver(PG_DEFAULT_DRIVER)
        self.qtIdent = pg_driver.qtIdent
        self.manager = pg_driver.connection_manager(
            kwargs['sid']
        )
        self.conn = self.manager.connection(did=kwargs['did'])
        self.datlastsysoid = 0
        if (
            self.manager.db_info is not None and
            kwargs['did'] in self.manager.db_info
        ):
            self.datlastsysoid = self.manager.db_info[kwargs['did']][
                'datlastsysoid']

        # Set template path for sql scripts
        if self.manager.server_type == 'gpdb':
            _temp = self.gpdb_template_path(self.manager.version)
        elif self.manager.server_type == 'ppas':
            _temp = self.ppas_template_path(self.manager.version)
        else:
            _temp = self.pg_template_path(self.manager.version)
        self.template_path = self.template_initial + '/' + _temp

        self.column_template_path = 'columns/sql/#{0}#'.format(
            self.manager.version)

        return f(*args, **kwargs)

    return wrap


class ViewNode(PGChildNodeView, VacuumSettings, SchemaDiffObjectCompare):
    """
    This class is responsible for generating routes for view node.

    Methods:
    -------
    * __init__(**kwargs)
      - Method is used to initialize the ViewNode and it's base view.

    * list()
      - This function is used to list all the view nodes within the
      collection.

    * nodes()
      - This function will used to create all the child node within the
        collection, Here it will create all the view node.

    * properties(gid, sid, did, scid)
      - This function will show the properties of the selected view node.

    * create(gid, sid, did, scid)
      - This function will create the new view object.

    * update(gid, sid, did, scid)
      - This function will update the data for the selected view node.

    * delete(self, gid, sid, scid):
      - This function will drop the view object

    * msql(gid, sid, did, scid)
      - This function is used to return modified SQL for the selected view
        node.

    * getSQL(data, scid)
      - This function will generate sql from model data

    * sql(gid, sid, did, scid):
      - This function will generate sql to show it in sql pane for the view
        node.

    * select_sql(gid, sid, did, scid, vid):
      - Returns select sql for Object

    * insert_sql(gid, sid, did, scid, vid):
      - Returns INSERT Script sql for the object

    * dependency(gid, sid, did, scid):
      - This function will generate dependency list show it in dependency
        pane for the selected view node.

    * dependent(gid, sid, did, scid):
      - This function will generate dependent list to show it in dependent
        pane for the selected view node.

    * compare(**kwargs):
      - This function will compare the view nodes from two
        different schemas.
    """
    node_type = view_blueprint.node_type

    parent_ids = [
        {'type': 'int', 'id': 'gid'},
        {'type': 'int', 'id': 'sid'},
        {'type': 'int', 'id': 'did'},
        {'type': 'int', 'id': 'scid'}
    ]
    ids = [
        {'type': 'int', 'id': 'vid'}
    ]

    operations = dict({
        'obj': [
            {'get': 'properties', 'delete': 'delete', 'put': 'update'},
            {'get': 'list', 'post': 'create', 'delete': 'delete'}
        ],
        'children': [{
            'get': 'children'
        }],
        'delete': [{'delete': 'delete'}, {'delete': 'delete'}],
        'nodes': [{'get': 'node'}, {'get': 'nodes'}],
        'sql': [{'get': 'sql'}],
        'msql': [{'get': 'msql'}, {'get': 'msql'}],
        'stats': [{'get': 'statistics'}],
        'dependency': [{'get': 'dependencies'}],
        'dependent': [{'get': 'dependents'}],
        'configs': [{'get': 'configs'}],
        'get_tblspc': [{'get': 'get_tblspc'}, {'get': 'get_tblspc'}],
        'select_sql': [{'get': 'select_sql'}, {'get': 'select_sql'}],
        'insert_sql': [{'get': 'insert_sql'}, {'get': 'insert_sql'}],
        'get_table_vacuum': [
            {'get': 'get_table_vacuum'},
            {'get': 'get_table_vacuum'}],
        'get_toast_table_vacuum': [
            {'get': 'get_toast_table_vacuum'},
            {'get': 'get_toast_table_vacuum'}]
    })

    keys_to_ignore = ['oid', 'schema', 'xmin']

    def __init__(self, *args, **kwargs):
        """
        Initialize the variables used by methods of ViewNode.
        """

        super(ViewNode, self).__init__(*args, **kwargs)

        self.manager = None
        self.conn = None
        self.template_path = None
        self.template_initial = 'views'

    @staticmethod
    def ppas_template_path(ver):
        """
        Returns the template path for PPAS servers.
        """
        return 'ppas/#{0}#'.format(ver)

    @staticmethod
    def pg_template_path(ver):
        """
        Returns the template path for PostgreSQL servers.
        """
        return 'pg/#{0}#'.format(ver)

    @staticmethod
    def gpdb_template_path(ver):
        """
        Returns the template path for GreenPlum servers.
        """
        return '#gpdb#{0}#'.format(ver)

    @check_precondition
    def list(self, gid, sid, did, scid):
        """
        Fetches all views properties and render into properties tab
        """
        SQL = render_template("/".join(
            [self.template_path, 'sql/properties.sql']), did=did, scid=scid)
        status, res = self.conn.execute_dict(SQL)

        if not status:
            return internal_server_error(errormsg=res)
        return ajax_response(
            response=res['rows'],
            status=200
        )

    @check_precondition
    def node(self, gid, sid, did, scid, vid):
        """
        Lists all views under the Views Collection node
        """
        SQL = render_template("/".join(
            [self.template_path, 'sql/nodes.sql']),
            vid=vid, datlastsysoid=self.datlastsysoid)
        status, rset = self.conn.execute_2darray(SQL)
        if not status:
            return internal_server_error(errormsg=rset)

        if len(rset['rows']) == 0:
            return gone(gettext("""Could not find the view."""))

        res = self.blueprint.generate_browser_node(
            rset['rows'][0]['oid'],
            scid,
            rset['rows'][0]['name'],
            icon="icon-view" if self.node_type == 'view'
            else "icon-mview"
        )

        return make_json_response(
            data=res,
            status=200
        )

    @check_precondition
    def nodes(self, gid, sid, did, scid):
        """
        Lists all views under the Views Collection node
        """
        res = []
        SQL = render_template("/".join(
            [self.template_path, 'sql/nodes.sql']), scid=scid)
        status, rset = self.conn.execute_2darray(SQL)
        if not status:
            return internal_server_error(errormsg=rset)

        for row in rset['rows']:
            res.append(
                self.blueprint.generate_browser_node(
                    row['oid'],
                    scid,
                    row['name'],
                    icon="icon-view" if self.node_type == 'view'
                    else "icon-mview"
                ))

        return make_json_response(
            data=res,
            status=200
        )

    @check_precondition
    def properties(self, gid, sid, did, scid, vid):
        """
        Fetches the properties of an individual view
        and render in the properties tab
        """
        status, res = self._fetch_properties(scid, vid)
        if not status:
            return res

        return ajax_response(
            response=res,
            status=200
        )

    def _fetch_properties(self, scid, vid):
        """
        This function is used to fetch the properties of the specified object
        :param scid:
        :param vid:
        :return:
        """
        SQL = render_template("/".join(
            [self.template_path, 'sql/properties.sql']
        ), vid=vid, datlastsysoid=self.datlastsysoid)
        status, res = self.conn.execute_dict(SQL)
        if not status:
            return False, internal_server_error(errormsg=res)

        if len(res['rows']) == 0:
            return False, gone(gettext("""Could not find the view."""))

        SQL = render_template("/".join(
            [self.template_path, 'sql/acl.sql']), vid=vid)
        status, dataclres = self.conn.execute_dict(SQL)
        if not status:
            return False, internal_server_error(errormsg=res)

        for row in dataclres['rows']:
            priv = parse_priv_from_db(row)
            res['rows'][0].setdefault(row['deftype'], []).append(priv)

        result = res['rows'][0]

        # sending result to formtter
        frmtd_reslt = self.formatter(result)

        # merging formated result with main result again
        result.update(frmtd_reslt)

        return True, result

    @staticmethod
    def formatter(result):
        """ This function formats output for security label & variables"""
        frmtd_result = dict()
        sec_lbls = []
        if 'seclabels' in result and result['seclabels'] is not None:
            for sec in result['seclabels']:
                import re
                sec = re.search(r'([^=]+)=(.*$)', sec)
                sec_lbls.append({
                    'provider': sec.group(1),
                    'label': sec.group(2)
                })

        frmtd_result.update({"seclabels": sec_lbls})
        return frmtd_result

    @check_precondition
    def create(self, gid, sid, did, scid):
        """
        This function will create a new view object
        """
        required_args = [
            'name',
            'definition'
        ]

        data = request.form if request.form else json.loads(
            request.data, encoding='utf-8'
        )
        for arg in required_args:
            if arg not in data:
                return make_json_response(
                    status=410,
                    success=0,
                    errormsg=gettext(
                        "Could not find the required parameter (%s)." % arg
                    )
                )
        try:
            SQL, nameOrError = self.getSQL(gid, sid, did, data)
            if SQL is None:
                return nameOrError
            SQL = SQL.strip('\n').strip(' ')
            status, res = self.conn.execute_scalar(SQL)
            if not status:
                return internal_server_error(errormsg=res)

            SQL = render_template("/".join(
                [self.template_path, 'sql/view_id.sql']), data=data)
            status, view_id = self.conn.execute_scalar(SQL)

            if not status:
                return internal_server_error(errormsg=res)

            # Get updated schema oid
            SQL = render_template("/".join(
                [self.template_path, 'sql/get_oid.sql']), vid=view_id)
            status, scid = self.conn.execute_scalar(SQL)

            if not status:
                return internal_server_error(errormsg=res)

            return jsonify(
                node=self.blueprint.generate_browser_node(
                    view_id,
                    scid,
                    data['name'],
                    icon="icon-view" if self.node_type == 'view'
                    else "icon-mview"
                )
            )
        except Exception as e:
            current_app.logger.exception(e)
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def update(self, gid, sid, did, scid, vid):
        """
        This function will update a view object
        """
        data = request.form if request.form else json.loads(
            request.data, encoding='utf-8'
        )
        try:
            SQL, name = self.getSQL(gid, sid, did, data, vid)
            if SQL is None:
                return name
            SQL = SQL.strip('\n').strip(' ')
            status, res = self.conn.execute_void(SQL)
            if not status:
                return internal_server_error(errormsg=res)

            SQL = render_template("/".join(
                [self.template_path, 'sql/view_id.sql']), data=data)
            status, res_data = self.conn.execute_dict(SQL)
            if not status:
                return internal_server_error(errormsg=res)

            view_id = res_data['rows'][0]['oid']
            new_view_name = res_data['rows'][0]['relname']

            # Get updated schema oid
            SQL = render_template("/".join(
                [self.template_path, 'sql/get_oid.sql']), vid=view_id)
            status, scid = self.conn.execute_scalar(SQL)
            if not status:
                return internal_server_error(errormsg=res)

            return jsonify(
                node=self.blueprint.generate_browser_node(
                    view_id,
                    scid,
                    new_view_name,
                    icon="icon-view" if self.node_type == 'view'
                    else "icon-mview"
                )
            )
        except Exception as e:
            current_app.logger.exception(e)
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def delete(self, gid, sid, did, scid, vid=None, only_sql=False):
        """
        This function will drop a view object
        """
        if vid is None:
            data = request.form if request.form else json.loads(
                request.data, encoding='utf-8'
            )
        else:
            data = {'ids': [vid]}

        # Below will decide if it's simple drop or drop with cascade call
        cascade = True if self.cmd == 'delete' else False

        try:
            for vid in data['ids']:
                # Get name for view from vid
                SQL = render_template(
                    "/".join([
                        self.template_path, 'sql/properties.sql'
                    ]),
                    did=did,
                    vid=vid,
                    datlastsysoid=self.datlastsysoid
                )
                status, res_data = self.conn.execute_dict(SQL)
                if not status:
                    return internal_server_error(errormsg=res_data)

                if not res_data['rows']:
                    return make_json_response(
                        success=0,
                        errormsg=gettext(
                            'Error: Object not found.'
                        ),
                        info=gettext(
                            'The specified view could not be found.\n'
                        )
                    )

                # drop view
                SQL = render_template(
                    "/".join([
                        self.template_path, 'sql/delete.sql'
                    ]),
                    nspname=res_data['rows'][0]['schema'],
                    name=res_data['rows'][0]['name'], cascade=cascade
                )

                if only_sql:
                    return SQL

                status, res = self.conn.execute_scalar(SQL)
                if not status:
                    return internal_server_error(errormsg=res)

            return make_json_response(
                success=1,
                info=gettext("View dropped")
            )

        except Exception as e:
            current_app.logger.exception(e)
            return internal_server_error(errormsg=str(e))

    def _get_schema(self, scid):
        """
        Returns Schema Name from its OID.

        Args:
            scid: Schema Id
        """
        SQL = render_template("/".join([self.template_path,
                                        'sql/get_schema.sql']), scid=scid)

        status, schema_name = self.conn.execute_scalar(SQL)

        if not status:
            return internal_server_error(errormsg=schema_name)

        return schema_name

    @check_precondition
    def msql(self, gid, sid, did, scid, vid=None):
        """
        This function returns modified SQL
        """
        data = {}
        for k, v in request.args.items():
            try:
                # comments should be taken as is because if user enters a
                # json comment it is parsed by loads which should not happen
                if k in ('comment',):
                    data[k] = v
                else:
                    data[k] = json.loads(v, encoding='utf-8')
            except ValueError:
                data[k] = v

        sql, nameOrError = self.getSQL(gid, sid, did, data, vid)
        if sql is None:
            return nameOrError

        sql = sql.strip('\n').strip(' ')

        if sql == '':
            sql = "--modified SQL"

        return make_json_response(
            data=sql,
            status=200
        )

    def getSQL(self, gid, sid, did, data, vid=None):
        """
        This function will generate sql from model data
        """
        if vid is not None:
            SQL = render_template("/".join(
                [self.template_path, 'sql/properties.sql']),
                vid=vid,
                datlastsysoid=self.datlastsysoid
            )
            status, res = self.conn.execute_dict(SQL)
            if not status:
                return None, internal_server_error(errormsg=res)
            if len(res['rows']) == 0:
                return None, gone(
                    gettext("Could not find the view on the server.")
                )
            old_data = res['rows'][0]

            if 'name' not in data:
                data['name'] = res['rows'][0]['name']
            if 'schema' not in data:
                data['schema'] = res['rows'][0]['schema']

            acls = []
            try:
                acls = render_template(
                    "/".join([self.template_path, 'sql/allowed_privs.json'])
                )
                acls = json.loads(acls, encoding='utf-8')
            except Exception as e:
                current_app.logger.exception(e)

            # Privileges
            for aclcol in acls:
                if aclcol in data:
                    allowedacl = acls[aclcol]

                    for key in ['added', 'changed', 'deleted']:
                        if key in data[aclcol]:
                            data[aclcol][key] = parse_priv_to_db(
                                data[aclcol][key], allowedacl['acl']
                            )

            try:
                SQL = render_template("/".join(
                    [self.template_path, 'sql/update.sql']), data=data,
                    o_data=old_data, conn=self.conn)
            except Exception as e:
                current_app.logger.exception(e)
                return None, internal_server_error(errormsg=str(e))
        else:
            required_args = [
                'name',
                'schema',
                'definition'
            ]
            for arg in required_args:
                if arg not in data:
                    return None, make_json_response(
                        data=gettext(" -- definition incomplete"),
                        status=200
                    )

            # Get Schema Name from its OID.
            if 'schema' in data and isinstance(data['schema'], int):
                data['schema'] = self._get_schema(data['schema'])

            acls = []
            try:
                acls = render_template(
                    "/".join([self.template_path, 'sql/allowed_privs.json'])
                )
                acls = json.loads(acls, encoding='utf-8')
            except Exception as e:
                current_app.logger.exception(e)

            # Privileges
            for aclcol in acls:
                if aclcol in data:
                    allowedacl = acls[aclcol]
                    data[aclcol] = parse_priv_to_db(
                        data[aclcol], allowedacl['acl']
                    )

            SQL = render_template("/".join(
                [self.template_path, 'sql/create.sql']), data=data)
            if data['definition']:
                SQL += "\n"
                SQL += render_template("/".join(
                    [self.template_path, 'sql/grant.sql']), data=data)

        return SQL, data['name'] if 'name' in data else old_data['name']

    def get_index_column_details(self, idx, data):
        """
        This functional will fetch list of column details for index

        Args:
            idx: Index OID
            data: Properties data

        Returns:
            Updated properties data with column details
        """

        self.index_temp_path = 'indexes'
        SQL = render_template("/".join([self.index_temp_path,
                                        'sql/#{0}#/column_details.sql'.format(
                                            self.manager.version)]), idx=idx)
        status, rset = self.conn.execute_2darray(SQL)
        if not status:
            return internal_server_error(errormsg=rset)

        # 'attdef' comes with quotes from query so we need to strip them
        # 'options' we need true/false to render switch ASC(false)/DESC(true)
        columns = []
        cols = []
        for row in rset['rows']:

            # We need all data as collection for ColumnsModel
            cols_data = {
                'colname': row['attdef'],
                'collspcname': row['collnspname'],
                'op_class': row['opcname'],
            }
            if row['options'][0] == 'DESC':
                cols_data['sort_order'] = True
            columns.append(cols_data)

            # We need same data as string to display in properties window
            # If multiple column then separate it by colon
            cols_str = row['attdef']
            if row['collnspname']:
                cols_str += ' COLLATE ' + row['collnspname']
            if row['opcname']:
                cols_str += ' ' + row['opcname']
            if row['options'][0] == 'DESC':
                cols_str += ' DESC'
            cols.append(cols_str)

        # Push as collection
        data['columns'] = columns
        # Push as string
        data['cols'] = ', '.join(cols)

        return data

    def get_trigger_column_details(self, tid, clist):
        """
        This function will fetch list of column for trigger

        Args:
            tid: Table OID
            clist: List of columns

        Returns:
            Updated properties data with column
        """

        self.trigger_temp_path = 'schemas/triggers'
        SQL = render_template("/".join([self.trigger_temp_path,
                                        'get_columns.sql']),
                              tid=tid, clist=clist)
        status, rset = self.conn.execute_2darray(SQL)
        if not status:
            return internal_server_error(errormsg=rset)
        # 'tgattr' contains list of columns from table used in trigger
        columns = []

        for row in rset['rows']:
            columns.append({'column': row['name']})

        return columns

    def get_rule_sql(self, vid, display_comments=True):
        """
        Get all non system rules of view node,
        generate their sql and render
        into sql tab
        """

        self.rule_temp_path = 'rules'
        SQL_data = ''
        SQL = render_template("/".join(
            [self.rule_temp_path, 'sql/properties.sql']), tid=vid)

        status, data = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=data)

        for rule in data['rows']:

            # Generate SQL only for non system rule
            if rule['name'] != '_RETURN':
                res = []
                SQL = render_template("/".join(
                    [self.rule_temp_path, 'sql/properties.sql']),
                    rid=rule['oid']
                )
                status, res = self.conn.execute_dict(SQL)
                res = parse_rule_definition(res)
                SQL = render_template("/".join(
                    [self.rule_temp_path, 'sql/create.sql']),
                    data=res, display_comments=display_comments)
                SQL_data += '\n'
                SQL_data += SQL
        return SQL_data

    def get_compound_trigger_sql(self, vid, display_comments=True):
        """
        Get all compound trigger nodes associated with view node,
        generate their sql and render into sql tab
        """
        SQL_data = ''
        if self.manager.server_type == 'ppas' \
                and self.manager.version >= 120000:

            from pgadmin.browser.server_groups.servers.databases.schemas.utils\
                import trigger_definition

            # Define template path
            self.ct_trigger_temp_path = 'compound_triggers'

            SQL = render_template("/".join(
                [self.ct_trigger_temp_path,
                 'sql/{0}/#{1}#/nodes.sql'.format(
                     self.manager.server_type, self.manager.version)]),
                tid=vid)

            status, data = self.conn.execute_dict(SQL)
            if not status:
                return internal_server_error(errormsg=data)

            for trigger in data['rows']:
                SQL = render_template("/".join(
                    [self.ct_trigger_temp_path,
                     'sql/{0}/#{1}#/properties.sql'.format(
                         self.manager.server_type, self.manager.version)]),
                    tid=vid,
                    trid=trigger['oid']
                )

                status, res = self.conn.execute_dict(SQL)
                if not status:
                    return internal_server_error(errormsg=res)

                if len(res['rows']) == 0:
                    continue
                res_rows = dict(res['rows'][0])
                res_rows['table'] = res_rows['relname']
                res_rows['schema'] = self.view_schema

                if len(res_rows['tgattr']) > 1:
                    columns = ', '.join(res_rows['tgattr'].split(' '))
                    SQL = render_template("/".join(
                        [self.ct_trigger_temp_path,
                         'sql/{0}/#{1}#/get_columns.sql'.format(
                             self.manager.server_type,
                             self.manager.version)]),
                        tid=trigger['oid'],
                        clist=columns)

                    status, rset = self.conn.execute_2darray(SQL)
                    if not status:
                        return internal_server_error(errormsg=rset)
                    # 'tgattr' contains list of columns from table
                    # used in trigger
                    columns = []

                    for col_row in rset['rows']:
                        columns.append(col_row['name'])

                    res_rows['columns'] = columns

                res_rows = trigger_definition(res_rows)
                SQL = render_template("/".join(
                    [self.ct_trigger_temp_path,
                     'sql/{0}/#{1}#/create.sql'.format(
                         self.manager.server_type, self.manager.version)]),
                    data=res_rows, display_comments=display_comments)
                SQL_data += '\n'
                SQL_data += SQL

        return SQL_data

    def get_trigger_sql(self, vid, display_comments=True):
        """
        Get all trigger nodes associated with view node,
        generate their sql and render
        into sql tab
        """
        if self.manager.server_type == 'gpdb':
            return ''

        from pgadmin.browser.server_groups.servers.databases.schemas.utils \
            import trigger_definition

        # Define template path
        self.trigger_temp_path = 'triggers'

        SQL_data = ''
        SQL = render_template("/".join(
            [self.trigger_temp_path,
             'sql/{0}/#{1}#/properties.sql'.format(
                 self.manager.server_type, self.manager.version)]),
            tid=vid)

        status, data = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=data)

        for trigger in data['rows']:
            SQL = render_template("/".join(
                [self.trigger_temp_path,
                 'sql/{0}/#{1}#/properties.sql'.format(
                     self.manager.server_type, self.manager.version)]),
                tid=vid,
                trid=trigger['oid']
            )

            status, res = self.conn.execute_dict(SQL)

            res_rows = dict(res['rows'][0])
            if res_rows['tgnargs'] > 1:
                # We know that trigger has more than 1
                # arguments, let's join them
                res_rows['tgargs'] = ', '.join(
                    res_rows['tgargs'])

            if len(res_rows['tgattr']) > 1:
                columns = ', '.join(res_rows['tgattr'].split(' '))
                res_rows['columns'] = self.get_trigger_column_details(
                    trigger['oid'], columns)
            res_rows = trigger_definition(res_rows)

            # It should be relname and not table, but in create.sql
            # (which is referred from many places) we have used
            # data.table and not data.relname so compatibility add new key as
            # table in res_rows.
            res_rows['table'] = res_rows['relname']
            res_rows['schema'] = self.view_schema

            # Get trigger function with its schema name
            SQL = render_template("/".join([
                self.trigger_temp_path,
                'sql/{0}/#{1}#/get_triggerfunctions.sql'.format(
                    self.manager.server_type, self.manager.version)]),
                tgfoid=res_rows['tgfoid'],
                show_system_objects=self.blueprint.show_system_objects)

            status, result = self.conn.execute_dict(SQL)
            if not status:
                return internal_server_error(errormsg=result)

            # Update the trigger function which we have fetched with
            # schemaname
            if (
                'rows' in result and len(result['rows']) > 0 and
                'tfunctions' in result['rows'][0]
            ):
                res_rows['tfunction'] = result['rows'][0]['tfunctions']

            # Format arguments
            if len(res_rows['custom_tgargs']) > 1:
                formatted_args = ["{0}".format(arg) for arg in
                                  res_rows['custom_tgargs']]
                res_rows['tgargs'] = ', '.join(formatted_args)

            SQL = render_template("/".join(
                [self.trigger_temp_path,
                 'sql/{0}/#{1}#/create.sql'.format(
                     self.manager.server_type, self.manager.version)]),
                data=res_rows, display_comments=display_comments)
            SQL_data += '\n'
            SQL_data += SQL

        return SQL_data

    def get_index_sql(self, did, vid, display_comments=True):
        """
        Get all index associated with view node,
        generate their sql and render
        into sql tab
        """

        self.index_temp_path = 'indexes'
        SQL_data = ''
        SQL = render_template("/".join(
            [self.index_temp_path,
             'sql/#{0}#/properties.sql'.format(self.manager.version)]),
            did=did,
            tid=vid)
        status, data = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=data)

        for index in data['rows']:
            res = []
            SQL = render_template("/".join(
                [self.index_temp_path,
                 'sql/#{0}#/properties.sql'.format(self.manager.version)]),
                idx=index['oid'],
                did=did,
                tid=vid
            )
            status, res = self.conn.execute_dict(SQL)

            data = dict(res['rows'][0])
            # Adding parent into data dict, will be using it while creating sql
            data['schema'] = data['nspname']
            data['table'] = data['tabname']

            # Add column details for current index
            data = self.get_index_column_details(index['oid'], data)

            SQL = render_template("/".join(
                [self.index_temp_path,
                 'sql/#{0}#/create.sql'.format(self.manager.version)]),
                data=data, display_comments=display_comments)
            SQL_data += '\n'
            SQL_data += SQL
        return SQL_data

    @check_precondition
    def sql(self, gid, sid, did, scid, vid, diff_schema=None,
            json_resp=True):
        """
        This function will generate sql to render into the sql panel
        """

        display_comments = True

        if not json_resp:
            display_comments = False

        SQL_data = ''
        SQL = render_template("/".join(
            [self.template_path, 'sql/properties.sql']),
            vid=vid,
            datlastsysoid=self.datlastsysoid
        )

        status, res = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=res)
        if len(res['rows']) == 0:
            return gone(
                gettext("Could not find the view on the server.")
            )

        result = res['rows'][0]
        if diff_schema:
            result['definition'] = result['definition'].replace(
                result['schema'],
                diff_schema)
            result['schema'] = diff_schema

        # sending result to formtter
        frmtd_reslt = self.formatter(result)

        # merging formated result with main result again
        result.update(frmtd_reslt)
        self.view_schema = result.get('schema')

        # Fetch all privileges for view
        SQL = render_template("/".join(
            [self.template_path, 'sql/acl.sql']), vid=vid)
        status, dataclres = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=res)

        for row in dataclres['rows']:
            priv = parse_priv_from_db(row)
            res['rows'][0].setdefault(row['deftype'], []).append(priv)

        result.update(res['rows'][0])

        acls = []
        try:
            acls = render_template(
                "/".join([self.template_path, 'sql/allowed_privs.json'])
            )
            acls = json.loads(acls, encoding='utf-8')
        except Exception as e:
            current_app.logger.exception(e)

        # Privileges
        for aclcol in acls:
            if aclcol in result:
                allowedacl = acls[aclcol]
                result[aclcol] = parse_priv_to_db(
                    result[aclcol], allowedacl['acl']
                )

        SQL = render_template("/".join(
            [self.template_path, 'sql/create.sql']),
            data=result,
            conn=self.conn,
            display_comments=display_comments
        )
        SQL += "\n"
        SQL += render_template("/".join(
            [self.template_path, 'sql/grant.sql']), data=result)

        SQL_data += SQL
        SQL_data += self.get_rule_sql(vid, display_comments)
        SQL_data += self.get_trigger_sql(vid, display_comments)
        SQL_data += self.get_compound_trigger_sql(vid, display_comments)
        SQL_data += self.get_index_sql(did, vid, display_comments)

        if not json_resp:
            return SQL_data
        return ajax_response(response=SQL_data)

    @check_precondition
    def get_tblspc(self, gid, sid, did, scid):
        """
        This function to return list of tablespaces
        """
        res = []
        try:
            SQL = render_template(
                "/".join([self.template_path, 'sql/get_tblspc.sql'])
            )
            status, rset = self.conn.execute_dict(SQL)
            if not status:
                return internal_server_error(errormsg=res)

            for row in rset['rows']:
                res.append(
                    {'label': row['spcname'], 'value': row['spcname']}
                )

            return make_json_response(
                data=res,
                status=200
            )

        except Exception as e:
            current_app.logger.exception(e)
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def dependents(self, gid, sid, did, scid, vid):
        """
        This function gets the dependents and returns an ajax response
        for the view node.

        Args:
            gid: Server Group ID
            sid: Server ID
            did: Database ID
            vid: View ID
        """
        dependents_result = self.get_dependents(self.conn, vid)
        return ajax_response(
            response=dependents_result,
            status=200
        )

    @check_precondition
    def dependencies(self, gid, sid, did, scid, vid):
        """
        This function gets the dependencies and returns an ajax response
        for the view node.

        Args:
            gid: Server Group ID
            sid: Server ID
            did: Database ID
            vid: View ID
        """
        dependencies_result = self.get_dependencies(self.conn, vid)
        return ajax_response(
            response=dependencies_result,
            status=200
        )

    @check_precondition
    def select_sql(self, gid, sid, did, scid, vid):
        """
        SELECT script sql for the object

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            vid: View Id

        Returns:
            SELECT Script sql for the object
        """
        SQL = render_template(
            "/".join([
                self.template_path, 'sql/properties.sql'
            ]),
            scid=scid, vid=vid, did=did,
            datlastsysoid=self.datlastsysoid
        )
        status, res = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=res)
        if len(res['rows']) == 0:
            return gone(
                gettext("Could not find the view on the server.")
            )
        data_view = res['rows'][0]

        SQL = render_template(
            "/".join([
                self.column_template_path, 'properties.sql'
            ]),
            scid=scid, tid=vid,
            datlastsysoid=self.datlastsysoid
        )
        status, data = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=res)

        columns = []

        # Now we have all list of columns which we need
        data = data['rows']
        for c in data:
            columns.append(self.qtIdent(self.conn, c['name']))

        if len(columns) > 0:
            columns = ", ".join(columns)
        else:
            columns = '*'

        sql = u"SELECT {0}\n\tFROM {1};".format(
            columns,
            self.qtIdent(self.conn, data_view['schema'], data_view['name'])
        )

        return ajax_response(response=sql)

    @check_precondition
    def insert_sql(self, gid, sid, did, scid, vid):
        """
        INSERT script sql for the object

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            foid: Foreign Table Id

        Returns:
            INSERT Script sql for the object
        """
        SQL = render_template(
            "/".join([
                self.template_path, 'sql/properties.sql'
            ]),
            scid=scid, vid=vid, did=did,
            datlastsysoid=self.datlastsysoid
        )
        status, res = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=res)
        if len(res['rows']) == 0:
            return gone(
                gettext("Could not find the view on the server.")
            )

        data_view = res['rows'][0]

        SQL = render_template(
            "/".join([
                self.column_template_path, 'properties.sql'
            ]),
            scid=scid, tid=vid,
            datlastsysoid=self.datlastsysoid
        )
        status, data = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=data)

        columns = []
        values = []

        # Now we have all list of columns which we need
        data = data['rows']
        for c in data:
            columns.append(self.qtIdent(self.conn, c['name']))
            values.append('?')

        if len(columns) > 0:
            columns = ", ".join(columns)
            values = ", ".join(values)
            sql = u"INSERT INTO {0}(\n\t{1})\n\tVALUES ({2});".format(
                self.qtIdent(
                    self.conn, data_view['schema'], data_view['name']
                ),
                columns, values
            )
        else:
            sql = gettext('-- Please create column(s) first...')

        return ajax_response(response=sql)

    @check_precondition
    def fetch_objects_to_compare(self, sid, did, scid, oid=None):
        """
        This function will fetch the list of all the views for
        specified schema id.

        :param sid: Server Id
        :param did: Database Id
        :param scid: Schema Id
        :return:
        """
        res = dict()

        if not oid:
            SQL = render_template("/".join([self.template_path,
                                            'sql/nodes.sql']), did=did,
                                  scid=scid, datlastsysoid=self.datlastsysoid)
            status, views = self.conn.execute_2darray(SQL)
            if not status:
                current_app.logger.error(views)
                return False

            for row in views['rows']:
                status, data = self._fetch_properties(scid, row['oid'])
                if status:
                    res[row['name']] = data
        else:
            status, data = self._fetch_properties(scid, oid)
            if not status:
                current_app.logger.error(data)
                return False
            res = data

        return res

    def get_sql_from_diff(self, gid, sid, did, scid, oid, data=None,
                          diff_schema=None, drop_sql=False):
        sql = ''
        if data:
            if diff_schema:
                data['schema'] = diff_schema
            sql, nameOrError = self.getSQL(gid, sid, did, data, oid)
        else:
            if drop_sql:
                sql = self.delete(gid=gid, sid=sid, did=did,
                                  scid=scid, vid=oid, only_sql=True)
            elif diff_schema:
                sql = self.sql(gid=gid, sid=sid, did=did, scid=scid, vid=oid,
                               diff_schema=diff_schema, json_resp=False)
            else:
                sql = self.sql(gid=gid, sid=sid, did=did, scid=scid, vid=oid,
                               json_resp=False)
        return sql


# Override the operations for materialized view
mview_operations = {
    'refresh_data': [{'put': 'refresh_data'}, {}]
}
mview_operations.update(ViewNode.operations)


class MViewNode(ViewNode, VacuumSettings):
    """
    This class is responsible for generating routes for
    materialized view node.

    Methods:
    -------
    * __init__(**kwargs)
      - Method is used to initialize the MView and it's base view.

    * create(gid, sid, did, scid)
      - Raise an error - we cannot create a material view.

    * update(gid, sid, did, scid)
      - This function will update the data for the selected material node

    * delete(self, gid, sid, scid):
      - Raise an error - we cannot delete a material view.

    * getSQL(data, scid)
      - This function will generate sql from model data

    * refresh_data(gid, sid, did, scid, vid):
      - This function will refresh view object
    """
    node_type = mview_blueprint.node_type
    operations = mview_operations

    def __init__(self, *args, **kwargs):
        """
        Initialize the variables used by methods of ViewNode.
        """

        super(MViewNode, self).__init__(*args, **kwargs)

        self.template_initial = 'mviews'

    @staticmethod
    def ppas_template_path(ver):
        """
        Returns the template path for EDB Advanced servers.
        """
        return 'ppas/9.3_plus'

    @staticmethod
    def pg_template_path(ver):
        """
        Returns the template path for PostgreSQL servers.
        """
        return 'pg/{0}'.format(
            '9.4_plus' if ver >= 90400 else
            '9.3_plus'
        )

    def getSQL(self, gid, sid, did, data, vid=None):
        """
        This function will generate sql from model data
        """
        if vid is not None:
            SQL = render_template("/".join(
                [self.template_path, 'sql/properties.sql']),
                did=did,
                vid=vid,
                datlastsysoid=self.datlastsysoid
            )
            status, res = self.conn.execute_dict(SQL)
            if not status:
                return None, internal_server_error(errormsg=res)
            if len(res['rows']) == 0:
                return None, gone(
                    gettext(
                        "Could not find the materialized view on the server.")
                )

            old_data = res['rows'][0]

            if 'name' not in data:
                data['name'] = res['rows'][0]['name']
            if 'schema' not in data:
                data['schema'] = res['rows'][0]['schema']

            # merge vacuum lists into one
            data['vacuum_data'] = {}
            data['vacuum_data']['changed'] = []
            data['vacuum_data']['reset'] = []

            # table vacuum: separate list of changed and reset data for
            if ('vacuum_table' in data):
                if ('changed' in data['vacuum_table']):
                    for item in data['vacuum_table']['changed']:
                        if 'value' in item.keys():
                            if item['value'] is None:
                                if old_data[item['name']] != item['value']:
                                    data['vacuum_data']['reset'].append(item)
                            else:
                                if (old_data[item['name']] is None or
                                    (float(old_data[item['name']]) != float(
                                        item['value']))):
                                    data['vacuum_data']['changed'].append(item)

            if (
                'autovacuum_enabled' in data and
                old_data['autovacuum_enabled'] is not None
            ):
                if (
                    data['autovacuum_enabled'] !=
                    old_data['autovacuum_enabled']
                ):
                    data['vacuum_data']['changed'].append(
                        {'name': 'autovacuum_enabled',
                         'value': data['autovacuum_enabled']})
            elif (
                'autovacuum_enabled' in data and
                'autovacuum_custom' in data and
                old_data['autovacuum_enabled'] is None and data[
                    'autovacuum_custom']):
                data['vacuum_data']['changed'].append(
                    {'name': 'autovacuum_enabled',
                     'value': data['autovacuum_enabled']})

            # toast autovacuum: separate list of changed and reset data
            if ('vacuum_toast' in data):
                if ('changed' in data['vacuum_toast']):
                    for item in data['vacuum_toast']['changed']:
                        if 'value' in item.keys():
                            toast_key = 'toast_' + item['name']
                            item['name'] = 'toast.' + item['name']
                            if item['value'] is None:
                                if old_data[toast_key] != item['value']:
                                    data['vacuum_data']['reset'].append(item)
                            else:
                                if (old_data[toast_key] is None or
                                    (float(old_data[toast_key]) != float(
                                        item['value']))):
                                    data['vacuum_data']['changed'].append(item)

            if (
                'toast_autovacuum_enabled' in data and
                old_data['toast_autovacuum_enabled'] is not None
            ):
                if (
                    data['toast_autovacuum_enabled'] !=
                    old_data['toast_autovacuum_enabled']
                ):
                    data['vacuum_data']['changed'].append(
                        {'name': 'toast.autovacuum_enabled',
                         'value': data['toast_autovacuum_enabled']})
            elif (
                'toast_autovacuum_enabled' in data and
                'toast_autovacuum' in data and
                old_data['toast_autovacuum_enabled'] is None and
                data['toast_autovacuum']
            ):
                data['vacuum_data']['changed'].append(
                    {'name': 'toast.autovacuum_enabled',
                     'value': data['toast_autovacuum_enabled']})

            acls = []
            try:
                acls = render_template(
                    "/".join([self.template_path, 'sql/allowed_privs.json'])
                )
                acls = json.loads(acls, encoding='utf-8')
            except Exception as e:
                current_app.logger.exception(e)

            # Privileges
            for aclcol in acls:
                if aclcol in data:
                    allowedacl = acls[aclcol]

                    for key in ['added', 'changed', 'deleted']:
                        if key in data[aclcol]:
                            data[aclcol][key] = parse_priv_to_db(
                                data[aclcol][key], allowedacl['acl']
                            )

            try:
                SQL = render_template("/".join(
                    [self.template_path, 'sql/update.sql']), data=data,
                    o_data=old_data, conn=self.conn)
            except Exception as e:
                current_app.logger.exception(e)
                return None, internal_server_error(errormsg=str(e))
        else:
            required_args = [
                'name',
                'schema',
                'definition'
            ]
            for arg in required_args:
                if arg not in data:
                    return None, make_json_response(
                        data=gettext(" -- definition incomplete"),
                        status=200
                    )

            # Get Schema Name from its OID.
            if 'schema' in data and isinstance(data['schema'], int):
                data['schema'] = self._get_schema(data['schema'])

            # merge vacuum lists into one
            vacuum_table = [item for item in data['vacuum_table']
                            if 'value' in item.keys() and
                            item['value'] is not None]
            vacuum_toast = [
                {'name': 'toast.' + item['name'], 'value': item['value']}
                for item in data['vacuum_toast']
                if 'value' in item.keys() and item['value'] is not None]

            # add table_enabled & toast_enabled settings
            if ('autovacuum_custom' in data and data['autovacuum_custom']):
                vacuum_table.append(
                    {
                        'name': 'autovacuum_enabled',
                        'value': str(data['autovacuum_enabled'])
                    }
                )
            if ('toast_autovacuum' in data and data['toast_autovacuum']):
                vacuum_table.append(
                    {
                        'name': 'toast.autovacuum_enabled',
                        'value': str(data['toast_autovacuum_enabled'])
                    }
                )

            # add vacuum_toast dict to vacuum_data only if
            # table & toast's custom autovacuum is enabled
            data['vacuum_data'] = []
            if (
                'autovacuum_custom' in data and
                data['autovacuum_custom'] is True
            ):
                data['vacuum_data'] = vacuum_table
            if (
                'toast_autovacuum' in data and
                data['toast_autovacuum'] is True
            ):
                data['vacuum_data'] += vacuum_toast

            acls = []
            try:
                acls = render_template(
                    "/".join([self.template_path, 'sql/allowed_privs.json'])
                )
                acls = json.loads(acls, encoding='utf-8')
            except Exception as e:
                current_app.logger.exception(e)

            # Privileges
            for aclcol in acls:
                if aclcol in data:
                    allowedacl = acls[aclcol]
                    data[aclcol] = parse_priv_to_db(
                        data[aclcol], allowedacl['acl']
                    )

            SQL = render_template("/".join(
                [self.template_path, 'sql/create.sql']), data=data)
            if data['definition']:
                SQL += "\n"
                SQL += render_template("/".join(
                    [self.template_path, 'sql/grant.sql']), data=data)
        return SQL, data['name'] if 'name' in data else old_data['name']

    @check_precondition
    def sql(self, gid, sid, did, scid, vid, diff_schema=None,
            json_resp=True):
        """
        This function will generate sql to render into the sql panel
        """

        display_comments = True

        if not json_resp:
            display_comments = False

        SQL_data = ''
        SQL = render_template("/".join(
            [self.template_path, 'sql/properties.sql']),
            did=did,
            vid=vid,
            datlastsysoid=self.datlastsysoid
        )

        status, res = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=res)
        if len(res['rows']) == 0:
            return gone(
                gettext("Could not find the materialized view on the server.")
            )

        result = res['rows'][0]

        if diff_schema:
            result['definition'] = result['definition'].replace(
                result['schema'],
                diff_schema)
            result['schema'] = diff_schema

        # sending result to formtter
        frmtd_reslt = self.formatter(result)

        # merging formated result with main result again
        result.update(frmtd_reslt)
        result['vacuum_table'] = self.parse_vacuum_data(
            self.conn, result, 'table')
        result['vacuum_toast'] = self.parse_vacuum_data(
            self.conn, result, 'toast')

        # merge vacuum lists into one
        vacuum_table = [item for item in result['vacuum_table']
                        if
                        'value' in item.keys() and item['value'] is not None]
        vacuum_toast = [
            {'name': 'toast.' + item['name'], 'value': item['value']}
            for item in result['vacuum_toast'] if
            'value' in item.keys() and item['value'] is not None]

        if 'autovacuum_custom' in result and result['autovacuum_custom']:
            vacuum_table.append(
                {
                    'name': 'autovacuum_enabled',
                    'value': str(result['autovacuum_enabled'])
                }
            )
        if 'toast_autovacuum' in result and result['toast_autovacuum']:
            vacuum_table.append(
                {
                    'name': 'toast.autovacuum_enabled',
                    'value': str(result['toast_autovacuum_enabled'])
                }
            )

        # add vacuum_toast dict to vacuum_data only if
        # toast's autovacuum is enabled
        if (
            'toast_autovacuum_enabled' in result and
            result['toast_autovacuum_enabled'] is True
        ):
            result['vacuum_data'] = vacuum_table + vacuum_toast
        else:
            result['vacuum_data'] = vacuum_table

        # Fetch all privileges for view
        SQL = render_template("/".join(
            [self.template_path, 'sql/acl.sql']), vid=vid)
        status, dataclres = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=res)

        for row in dataclres['rows']:
            priv = parse_priv_from_db(row)
            res['rows'][0].setdefault(row['deftype'], []).append(priv)

        result.update(res['rows'][0])

        acls = []
        try:
            acls = render_template(
                "/".join([self.template_path, 'sql/allowed_privs.json'])
            )
            acls = json.loads(acls, encoding='utf-8')
        except Exception as e:
            current_app.logger.exception(e)

        # Privileges
        for aclcol in acls:
            if aclcol in result:
                allowedacl = acls[aclcol]
                result[aclcol] = parse_priv_to_db(
                    result[aclcol], allowedacl['acl']
                )

        SQL = render_template("/".join(
            [self.template_path, 'sql/create.sql']),
            data=result,
            conn=self.conn,
            display_comments=display_comments
        )
        SQL += "\n"
        SQL += render_template("/".join(
            [self.template_path, 'sql/grant.sql']), data=result)

        SQL_data += SQL
        SQL_data += self.get_rule_sql(vid, display_comments)
        SQL_data += self.get_trigger_sql(vid, display_comments)
        SQL_data += self.get_index_sql(did, vid, display_comments)
        SQL_data = SQL_data.strip('\n')

        if not json_resp:
            return SQL_data
        return ajax_response(response=SQL_data)

    @check_precondition
    def get_table_vacuum(self, gid, sid, did, scid):
        """
        Fetch the default values for autovacuum
        fields, return an array of
          - label
          - name
          - setting
        values
        """

        res = self.get_vacuum_table_settings(self.conn, sid)
        return ajax_response(
            response=res,
            status=200
        )

    @check_precondition
    def get_toast_table_vacuum(self, gid, sid, did, scid):
        """
        Fetch the default values for autovacuum
        fields, return an array of
          - label
          - name
          - setting
        values
        """
        res = self.get_vacuum_toast_settings(self.conn, sid)

        return ajax_response(
            response=res,
            status=200
        )

    @check_precondition
    def properties(self, gid, sid, did, scid, vid):
        """
        Fetches the properties of an individual view
        and render in the properties tab
        """
        status, res = self._fetch_properties(did, scid, vid)
        if not status:
            return res

        return ajax_response(
            response=res,
            status=200
        )

    def _fetch_properties(self, did, scid, vid):
        """
        This function is used to fetch the properties of the specified object
        :param did:
        :param scid:
        :param vid:
        :return:
        """
        SQL = render_template("/".join(
            [self.template_path, 'sql/properties.sql']
        ), did=did, vid=vid, datlastsysoid=self.datlastsysoid)
        status, res = self.conn.execute_dict(SQL)
        if not status:
            return False, internal_server_error(errormsg=res)

        if len(res['rows']) == 0:
            return False, gone(
                gettext("""Could not find the materialized view."""))

        SQL = render_template("/".join(
            [self.template_path, 'sql/acl.sql']), vid=vid)
        status, dataclres = self.conn.execute_dict(SQL)
        if not status:
            return False, internal_server_error(errormsg=res)

        for row in dataclres['rows']:
            priv = parse_priv_from_db(row)
            res['rows'][0].setdefault(row['deftype'], []).append(priv)

        result = res['rows'][0]

        # sending result to formtter
        frmtd_reslt = self.formatter(result)

        # merging formated result with main result again
        result.update(frmtd_reslt)

        result['vacuum_table'] = self.parse_vacuum_data(
            self.conn, result, 'table')
        result['vacuum_toast'] = self.parse_vacuum_data(
            self.conn, result, 'toast')

        return True, result

    @check_precondition
    def refresh_data(self, gid, sid, did, scid, vid):
        """
        This function will refresh view object
        """

        # Below will decide if it's refresh data or refresh concurrently
        data = request.form if request.form else json.loads(
            request.data, encoding='utf-8'
        )

        is_concurrent = json.loads(data['concurrent'])
        with_data = json.loads(data['with_data'])

        try:

            # Fetch view name by view id
            SQL = render_template("/".join(
                [self.template_path, 'sql/get_view_name.sql']), vid=vid)
            status, res = self.conn.execute_dict(SQL)
            if not status:
                return internal_server_error(errormsg=res)

            # Refresh view
            SQL = render_template(
                "/".join([self.template_path, 'sql/refresh.sql']),
                name=res['rows'][0]['name'],
                nspname=res['rows'][0]['schema'],
                is_concurrent=is_concurrent,
                with_data=with_data
            )
            status, res_data = self.conn.execute_dict(SQL)
            if not status:
                return internal_server_error(errormsg=res_data)

            return make_json_response(
                success=1,
                info=gettext("View refreshed"),
                data={
                    'id': vid,
                    'sid': sid,
                    'gid': gid,
                    'did': did
                }
            )

        except Exception as e:
            current_app.logger.exception(e)
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def fetch_objects_to_compare(self, sid, did, scid, oid=None):
        """
        This function will fetch the list of all the mviews for
        specified schema id.

        :param sid: Server Id
        :param did: Database Id
        :param scid: Schema Id
        :return:
        """
        res = dict()
        SQL = render_template("/".join([self.template_path,
                                        'sql/nodes.sql']), did=did,
                              scid=scid, datlastsysoid=self.datlastsysoid)
        status, rset = self.conn.execute_2darray(SQL)
        if not status:
            return internal_server_error(errormsg=res)

        for row in rset['rows']:
            status, data = self._fetch_properties(did, scid, row['oid'])
            if status:
                res[row['name']] = data

        return res


SchemaDiffRegistry(view_blueprint.node_type, ViewNode)
ViewNode.register_node_view(view_blueprint)
SchemaDiffRegistry(mview_blueprint.node_type, MViewNode)
MViewNode.register_node_view(mview_blueprint)
