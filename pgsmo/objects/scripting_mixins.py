# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta, abstractmethod
from typing import Tuple

import pgsmo.utils.templating as templating


class ScriptableCreate(metaclass=ABCMeta):
    def __init__(self, template_root: str, server_version: Tuple[int, int, int]):
        self.server_version: Tuple[int, int, int] = server_version
        self.template_root: str = template_root

    def create_script(self):
        """Generates a script that creates an object of the inheriting type"""
        data = self._create_query_data
        return templating.render_template(
            templating.get_template_path(self.template_root, 'create.sql', self.server_version),
            **data
        )

    @property
    @abstractmethod
    def _create_query_data(self) -> dict:
        pass
