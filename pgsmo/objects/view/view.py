# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path

from smo.common.node_object import NodeCollection, NodeObject
from pgsmo.objects.view.view_base import ViewBase
from pgsmo.objects.table_objects.rule import Rule
from pgsmo.objects.table_objects.trigger import Trigger
from pgsmo.objects.server import PGserver    # noqa
import smo.utils.templating as templating


class View(ViewBase):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'view_templates')

    @classmethod
    def _template_root(cls, server: PGserver):
        return os.path.join(cls.TEMPLATE_ROOT, server.server_type)

    def __init__(self, server: PGserver, parent: NodeObject, name: str):
        ViewBase.__init__(self, server, parent, name)
        self._rules: NodeCollection[Rule] = self._register_child_collection(Rule)
        self._triggers: NodeCollection[Trigger] = self._register_child_collection(Trigger)

    @property
    def rules(self) -> NodeCollection[Rule]:
        return self._rules

    @property
    def triggers(self) -> NodeCollection[Trigger]:
        return self._triggers
