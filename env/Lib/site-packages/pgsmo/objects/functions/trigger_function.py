# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path

import smo.utils.templating as templating
from pgsmo.objects.functions.function_base import FunctionBase
from pgsmo.objects.server import server as s  # noqa


class TriggerFunction(FunctionBase):
    TEMPLATE_ROOT = templating.get_template_root(__file__, "templates_trigger_funcs")

    @classmethod
    def _template_root(cls, server: "s.Server"):
        return path.join(cls.TEMPLATE_ROOT, server.server_type)
