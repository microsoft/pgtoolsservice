# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path

from pgsmo.objects.functions.function_base import FunctionBase
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


class Function(FunctionBase):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_functions')

    @classmethod
    def _template_path(cls, conn: querying.ServerConnection):
        return path.join(cls.TEMPLATE_ROOT, conn.server_type)
