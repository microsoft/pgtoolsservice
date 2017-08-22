# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta, abstractmethod
from typing import List, Tuple

import pgsmo.utils.templating as templating


class ScriptableCreate(metaclass=ABCMeta):
    def __init__(self, template_root: str, macro_root: List[str], server_version: Tuple[int, int, int]):
        # NOTE: These member variables have a "cmx" prefix to prevent interaction with child class implementations
        self._cmx_macro_root: List[str] = macro_root
        self._cmx_server_version: Tuple[int, int, int] = server_version
        self._cmx_template_root: str = template_root

    def create_script(self):
        """Generates a script that creates an object of the inheriting type"""
        data = self._create_query_data()
        return templating.render_template(
            templating.get_template_path(self._cmx_template_root, 'create.sql', self._cmx_server_version),
            self._cmx_macro_root,
            **data
        )

    @abstractmethod
    def _create_query_data(self) -> dict:
        pass
