# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional

import pgsmo.utils as utils

TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Tablespace:
    @staticmethod
    def get_tablespaces_for_server(conn: utils.querying.ConnectionWrapper) -> List['Tablespace']:
        sql = utils.templating.render_template(
            utils.templating.get_template_path(TEMPLATE_ROOT, 'nodes.sql', conn.version)
        )
        cols, rows = utils.querying.execute_dict(conn, sql)

        return [Tablespace._from_node_query(**row) for row in rows]

    @classmethod
    def _from_node_query(cls, **kwargs):
        tablespace = cls()
        tablespace._oid = kwargs['oid']
        tablespace._name = kwargs['name']
        tablespace._owner = kwargs['owner']

        return tablespace

    def __init__(self):
        # Declare basic properties
        self._oid: Optional[int] = None
        self._name: Optional[str] = None
        self._owner: Optional[int] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def oid(self) -> Optional[int]:
        return self._oid

    @property
    def owner(self) -> Optional[int]:
        return self._owner
