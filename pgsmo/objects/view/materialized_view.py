# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path

from smo.common.node_object import NodeCollection, NodeObject
from pgsmo.objects.view.view_base import ViewBase
from pgsmo.objects.table_objects.index import Index
from pgsmo.objects.server import server as s    # noqa
import smo.utils.templating as templating


class MaterializedView(ViewBase):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'materialized_view_templates')

    @classmethod
    def _template_root(cls, server: 's.Server'):
        return os.path.join(cls.TEMPLATE_ROOT, server.server_type)

    def __init__(self, server: 's.Server', parent: NodeObject, name: str) -> None:
        ViewBase.__init__(self, server, parent, name)
        self._indexes: NodeCollection[Index] = self._register_child_collection(Index)

    @property
    def indexes(self) -> NodeCollection[Index]:
        return self._indexes
