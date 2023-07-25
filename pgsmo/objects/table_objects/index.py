# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from smo.common.node_object import NodeObject
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server import server as s    # noqa
import smo.utils.templating as templating


class Index(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'index')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject, **kwargs) -> 'Index':
        """
        Creates a new Index object based on the results of a nodes query
        :param server: Server that owns the index
        :param parent: Parent object of the Index. Should be Table/View
        :param kwargs: Parameters for the index
        Kwargs:
            name str: The name of the index
            oid int: Object ID of the index
        :return: Instance of the Index
        """
        idx = cls(server, parent, kwargs['name'])
        idx._oid = kwargs['oid']
        idx._is_clustered = kwargs['indisclustered']
        idx._is_primary = kwargs['indisprimary']
        idx._is_unique = kwargs['indisunique']
        idx._is_valid = kwargs['indisvalid']
        idx._schema = idx.parent.schema # Parent will be either table or view, which both have schema defined
        return idx

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
        """
        Initializes a new instance of an Index
        :param server: Server that owns the index
        :param parent: Parent object of the index. Should be Table/View
        :param name: Name of the index
        """
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

        # Object Properties
        self._is_clustered: Optional[bool] = None
        self._is_primary: Optional[bool] = None
        self._is_unique: Optional[bool] = None
        self._is_valid: Optional[bool] = None
        self._is_concurrent: Optional[bool] = None
        self._schema: Optional[str] = None

    # PROPERTIES ###########################################################
    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def schema(self):
        return self._schema

    @property
    def is_clustered(self):
        return self._is_clustered

    @property
    def is_valid(self) -> Optional[bool]:
        return self._is_valid

    @property
    def is_unique(self):
        return self._is_unique

    @property
    def is_primary(self):
        return self._is_primary

    @property
    def is_concurrent(self):
        return self._is_concurrent

    @property
    def amname(self):
        return self._full_properties["amname"]

    @property
    def columns(self):
        return self._full_properties["columns"]

    @property
    def fillfactor(self):
        return self._full_properties["fillfactor"]

    @property
    def spcname(self):
        return self._full_properties["spcname"]

    @property
    def indconstraint(self):
        return self._full_properties["indconstraint"]

    @property
    def mode(self):
        return self._full_properties["mode"]

    @property
    def index(self):
        return self._full_properties["index"]

    @property
    def cascade(self):
        return self._full_properties["cascade"]

    @property
    def description(self):
        return self._full_properties["description"]

    @property
    def extended_vars(self):
        return {
            'idx': self.oid,
            'tid': self.parent.oid, # Table/view OID
            'did': self.parent.parent.oid # Database OID
        }
    # IMPLEMENTATION DETAILS ###############################################

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        create_query_data = {
            "data": {
                "indisunique": self.is_unique,
                "isconcurrent": self.is_concurrent,
                "name": self.name,
                "schema": self.parent.schema,
                "table": self.parent.name,
                "amname": self.amname,
                "fillfactor": self.fillfactor,
                "spcname": self.spcname,
                "indconstraint": self.indconstraint
            },
            "mode": "create"
        }

        self.get_column_details(create_query_data['data'], create_query_data['mode'])
        if self._mxin_server_version[0] >= 11:
            self.get_include_details(create_query_data['data'])

        return create_query_data


    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "data": {
                "nspname": self.parent.schema,
                "name": self.name
            },
            "cascade": self.cascade
        }

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        return {
            "data": {
                "name": self.name,
                "schema": self.parent.schema,
                "fillfactor": self.fillfactor,
                "spcname": self.spcname,
                "indisclustered": self.is_clustered,
                "table": self.parent.name,
                "description": self.description
            },
            "o_data": {
                "name": "",
                "fillfactor": "",
                "spcname": "",
                "indisclustered": "",
                "description": ""
            }
        }

    ##########################################################################
    #
    # pgAdmin 4 - PostgreSQL Tools
    #
    # Copyright (C) 2013 - 2017, The pgAdmin Development Team
    # This software is released under the PostgreSQL Licence
    #
    ##########################################################################

    def get_column_details(self, data, mode='properties'):
        """
        This functional will fetch list of column for index.

        :param self: Index Object
        :param data: Data
        :param mode: 'create' or 'properties'
        :return:
        """

        # SQL = render_template(
        #     "/".join([template_path, 'column_details.sql']), idx=idx
        # )

        sql = templating.render_template(
            templating.get_template_path(self._mxin_template_root, 'column_details.sql', self._mxin_server_version),
            self._mxin_macro_root,
            idx=self.oid
        )

        cols, rows = self._server.connection.execute_dict(sql)

        # Remove column if duplicate column is present in list.
        rows = [i for n, i in enumerate(rows) if
                        i not in rows[n + 1:]]

        # 'attdef' comes with quotes from query so we need to strip them
        # 'options' we need true/false to render switch ASC(false)/DESC(true)
        columns = []
        cols = []
        for row in rows:
            # We need all data as collection for ColumnsModel
            # we will not strip down colname when using in SQL to display
            cols_data = {
                'colname': row['attdef'] if mode == 'create' else
                row['attdef'].strip('"'),
                'collspcname': row['collnspname'],
                'op_class': row['opcname'],
            }

            # ASC/DESC and NULLS works only with btree indexes
            if 'amname' in data and data['amname'] == 'btree':
                cols_data['sort_order'] = False
                if row['options'][0] == 'DESC':
                    cols_data['sort_order'] = True

                cols_data['nulls'] = False
                if row['options'][1].split(" ")[1] == 'FIRST':
                    cols_data['nulls'] = True

            columns.append(cols_data)

            # We need same data as string to display in properties window
            # If multiple column then separate it by colon
            cols_str = ''
            cols_str += self._get_column_property_display_data(row, row['attdef'], data)

            cols.append(cols_str)

        # Push as collection
        data['columns'] = columns
        # Push as string
        data['columns_csv'] = ', '.join(cols)

        return data

    def get_include_details(self, data):
        """
        This functional will fetch list of include details for index
        supported with Postgres 11+

        :param conn: Connection object
        :param idx: Index ID
        :param data: data
        :param template_path: Optional template path
        :return:
        """
        sql = templating.render_template(
            templating.get_template_path(self._mxin_template_root, 'include_details.sql', self._mxin_server_version),
            self._mxin_macro_root,
            idx=self.oid
        )

        cols, rows = self._server.connection.execute_dict(sql)

        # Push as collection
        data['include'] = [col['colname'] for col in rows]

        return data
    
    @staticmethod
    def _get_column_property_display_data(row, col_str, data):
        """
        This function is used to get the columns data.
        :param row:
        :param col_str:
        :param data:
        :return:
        """
        if row['collnspname']:
            col_str += ' COLLATE ' + row['collnspname']
        if row['opcname']:
            col_str += ' ' + row['opcname']

        # ASC/DESC and NULLS works only with btree indexes
        if 'amname' in data and data['amname'] == 'btree':
            # Append sort order
            col_str += ' ' + row['options'][0]
            # Append nulls value
            col_str += ' ' + row['options'][1]

        return col_str
