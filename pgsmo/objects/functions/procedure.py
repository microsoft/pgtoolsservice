# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path

from pgsmo.objects.functions.function_base import FunctionBase
from pgsmo.objects.server import server as s    # noqa
import smo.utils.templating as templating


class Procedure(FunctionBase):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_procedures')

    @classmethod
    def _template_root(cls, server: 's.Server'):
        return os.path.join(cls.TEMPLATE_ROOT, server.server_type)
