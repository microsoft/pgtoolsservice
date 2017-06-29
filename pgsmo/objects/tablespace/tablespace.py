# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional

import pgsmo.utils as utils

TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Tablespace:
    @classmethod
    def get_tablespaces_for_server(cls, conn: utils.querying.ConnectionWrapper) -> List['Tablespace']:
        """
        Creates a list of tablespaces that belong to the server. Intended to be called by Server class
        :param conn: Connection to a server to use to lookup the information
        :return: List of tablespaces for the given server
        """
        sql = utils.templating.render_template(
            utils.templating.get_template_path(TEMPLATE_ROOT, 'nodes.sql', conn.version)
        )
        cols, rows = utils.querying.execute_dict(conn, sql)

        return [cls._from_node_query(conn, **row) for row in rows]

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ConnectionWrapper, **kwargs) -> 'Tablespace':
        """
        Creates a tablespace from a row of a nodes query result
        :param conn: Connection to a server to use to lookup the information
        :param kwargs: Row from a node query for a list of
        :return: A Tablespace instance
        """
        tablespace = cls()
        tablespace._conn = conn

        tablespace._oid = kwargs['oid']
        tablespace._name = kwargs['name']
        tablespace._owner = kwargs['owner']

        return tablespace

    def __init__(self):
        """Initializes internal state of a Tablespace"""
        self._conn: Optional[utils.querying.ConnectionWrapper] = None

        # Declare basic properties
        self._oid: Optional[int] = None
        self._name: Optional[str] = None
        self._owner: Optional[int] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def name(self) -> Optional[str]:
        """Name of the tablespace"""
        return self._name

    @property
    def oid(self) -> Optional[int]:
        """Object ID of the tablespace"""
        return self._oid

    @property
    def owner(self) -> Optional[int]:
        """Object ID of the user that owns the tablespace"""
        return self._owner
