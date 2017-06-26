# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

import pgsmo.utils as utils

TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Column:
    @staticmethod
    def get_columns_for_table(conn: utils.querying.ConnectionWrapper, tid: int, fetch: bool=False):
        # Execute query to get list of columns
        sql = utils.templating.render_template(
            utils.templating.get_template_path(TEMPLATE_ROOT, 'nodes.sql', conn.version),
            tid=tid
            # TODO: Add show system objs support
        )
        cols, rows = utils.querying.execute_dict(conn, sql)

        return [Column._from_node_query(conn, row['oid'], row['name'], row['datatype'], **row) for row in rows]

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ConnectionWrapper,
                         col_id: int, col_name: str, col_datatype: str,
                         **kwargs):
        """
        Creates a new Column object based on the the results from the column nodes query
        :param conn: Connection used to execute the column nodes query
        :param kwargs: Optional parameters for the column
        :params col_id: Object ID of the column
        :params col_name: Name of the column
        :params col_datatype: Type of the column
        Kwargs:
            not_null bool: Whether or not null is allowed for the column
            has_default_value bool: Whether or not the column has a default value constraint
        :return: Instance of the Column
        """
        col = cls(col_name, col_datatype)

        # Assign the mandatory properties
        col._cid = col_id
        col._conn = conn

        # Assign the optional properties
        col._has_default_value = kwargs.get('has_default_value')
        col._not_null = kwargs.get('not_null')

        return col

    def __init__(self, name: str, datatype: str):
        """
        Initializes a new instance of a Column
        :param name: Name of the column
        :param datatype: Type of the column
        """
        self._name: str = name
        self._datatype: str = datatype

        # Declare the optional parameters
        self._conn: Optional[utils.querying.ConnectionWrapper] = None
        self._cid: Optional[int] = None
        self._has_default_value: Optional[bool] = None
        self._not_null: Optional[bool] = None

    # PROPERTIES ###########################################################
    @property
    def datatype(self) -> str:
        return self._datatype

    @property
    def has_default_value(self) -> Optional[bool]:
        return self._has_default_value

    @property
    def name(self) -> str:
        return self._name

    @property
    def not_null(self) -> Optional[bool]:
        return self._not_null

    @property
    def oid(self) -> Optional[int]:
        return self._cid

    # METHODS ##############################################################
    def refresh(self):
        self._fetch_properties()

    # IMPLEMENTATION DETAILS ###############################################
    def _fetch_properties(self):
        pass
