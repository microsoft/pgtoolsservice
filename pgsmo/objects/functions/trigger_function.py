# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsmo.objects.functions.function_base import FunctionBase
import pgsmo.utils.templating as templating


class TriggerFunction(FunctionBase):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_functions')

    @classmethod
    def _template_path(cls):
        return cls.TEMPLATE_ROOT
