# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path
from typing import List, Optional

from pgsmo.objects.table.table import Table
from pgsmo.objects.view.view import View
import pgsmo.utils as utils


TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Role:
    @staticmethod
    def get_roles_for_server(conn: utils.querying.ConnectionWrapper):
        sql = utils.templating.render_template(
            utils.templating.get_template_path(TEMPLATE_ROOT, 'nodes.sql', conn.version),
        )
        cols, rows = utils.querying.execute_dict(conn, sql)

        return [Role._from_node_query(conn, **row) for row in rows]

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ConnectionWrapper, **kwargs):
        role = cls()
        role._conn = conn

        # Define values from node query
        role._oid = kwargs.get('oid')
        role._name = kwargs.get('rolname')
        role._can_login = kwargs.get('rolcanlogin')
        role._super = kwargs.get('rolsuper')

        return role

    def __init__(self):
        self._conn: Optional[utils.querying.ConnectionWrapper] = None

        # Declare basic properties
        self._oid: Optional[int] = None
        self._name: Optional[str] = None
        self._can_login: Optional[bool] = None
        self._super: Optional[bool] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def can_login(self) -> Optional[bool]:
        return self._can_login

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def oid(self) -> Optional[int]:
        return self._oid

    @property
    def super(self) -> Optional[bool]:
        return self._super