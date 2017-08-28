# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta, abstractmethod
from typing import List, Tuple

import pgsmo.utils.templating as templating


class ScriptableBase(metaclass=ABCMeta):
    def __init__(self, template_root: str, macro_root: List[str], server_version: Tuple[int, int, int]):
        # NOTE: These member variables have a "mxin" prefix to prevent interaction with child class implementations
        self._mxin_macro_root: List[str] = macro_root
        self._mxin_server_version: Tuple[int, int, int] = server_version
        self._mxin_template_root: str = template_root


class ScriptableCreate(ScriptableBase, metaclass=ABCMeta):
    def __init__(self, template_root: str, macro_root: List[str], server_version: Tuple[int, int, int]):
        super(ScriptableCreate, self).__init__(template_root, macro_root, server_version)

    def create_script(self):
        """Generates a script that creates an object of the inheriting type"""
        data = self._create_query_data()
        return templating.render_template(
            templating.get_template_path(self._mxin_template_root, 'create.sql', self._mxin_server_version),
            self._mxin_macro_root,
            **data
        )

    @abstractmethod
    def _create_query_data(self) -> dict:
        pass


class ScriptableDelete(ScriptableBase, metaclass=ABCMeta):
    def __init__(self, template_root: str, macro_root: List[str], server_version: Tuple[int, int, int]):
        super(ScriptableDelete, self).__init__(template_root, macro_root, server_version)

    def delete_script(self):
        """Generates a script that creates an object of the inheriting type"""
        data = self._delete_query_data()
        return templating.render_template(
            templating.get_template_path(self._mxin_template_root, 'delete.sql', self._mxin_server_version),
            self._mxin_macro_root,
            **data
        )

    @abstractmethod
    def _delete_query_data(self) -> dict:
        pass


class ScriptableUpdate(ScriptableBase, metaclass=ABCMeta):
    def __init__(self, template_root: str, macro_root: List[str], server_version: Tuple[int, int, int]):
        super(ScriptableUpdate, self).__init__(template_root, macro_root, server_version)

    def update_script(self):
        """Generates a script that creates an object of the inheriting type"""
        data = self._update_query_data()
        return templating.render_template(
            templating.get_template_path(self._mxin_template_root, 'update.sql', self._mxin_server_version),
            self._mxin_macro_root,
            **data
        )

    @abstractmethod
    def _update_query_data(self) -> dict:
        pass
