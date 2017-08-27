# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta, abstractmethod
from typing import Callable, Type
import unittest
import unittest.mock as mock

from pgsmo.objects.scripting_mixins import ScriptableBase, ScriptableCreate, ScriptableDelete, ScriptableUpdate


TEMPLATE_ROOT = 'template_root'
MACRO_ROOT = ['macro_root']
SERVER_VERSION = (1, 1, 1)
QUERY_DATA = {}


class ScriptableTestBase(metaclass=ABCMeta):
    unittest = unittest.TestCase('__init__')

    @property
    @abstractmethod
    def class_for_test(self) -> Type[ScriptableBase]:
        pass

    @property
    @abstractmethod
    def expected_template(self) -> str:
        pass

    @property
    @abstractmethod
    def script_lambda(self) -> Callable[[ScriptableBase], str]:
        pass

    # TEST METHODS #########################################################
    def test_init(self):
        # If: I create a mock scriptable
        class_ = self.class_for_test
        mock_obj = class_()

        # Then: The internal state should be appropriately setup
        self.unittest.assertEqual(mock_obj._mxin_macro_root, MACRO_ROOT)
        self.unittest.assertEqual(mock_obj._mxin_server_version, SERVER_VERSION)
        self.unittest.assertEqual(mock_obj._mxin_template_root, TEMPLATE_ROOT)

    def test_script(self):
        # Setup:
        # ... Create a mock scriptable
        class_ = self.class_for_test
        mock_obj = class_()

        # ... Patch out the templating code
        mock_path = 'path.sql'
        mock_output = 'sql'
        template_path_path = "pgsmo.objects.scripting_mixins.templating.get_template_path"
        template_path_mock = mock.MagicMock(return_value=mock_path)
        template_render_path = "pgsmo.objects.scripting_mixins.templating.render_template"
        template_render_mock = mock.MagicMock(return_value=mock_output)

        with(mock.patch(template_path_path, template_path_mock, create=True)):
            with(mock.patch(template_render_path, template_render_mock, create=True)):
                # If: I get a script
                result = self.script_lambda(mock_obj)

        # Then:
        # ... The template mocks should have been called
        template_path_mock.assert_called_once_with(TEMPLATE_ROOT, self.expected_template, SERVER_VERSION)
        template_render_mock.assert_called_once_with(mock_path, MACRO_ROOT, **QUERY_DATA)

        # ... The output should match the expected output
        self.unittest.assertEqual(result, mock_output)


class TestScriptableCreate(ScriptableTestBase, unittest.TestCase):
    @property
    def class_for_test(self) -> Type[ScriptableBase]:
        return self._MockScriptableCreate

    @property
    def expected_template(self) -> str:
        return 'create.sql'

    @property
    def script_lambda(self):
        return lambda obj: obj.create_script()

    class _MockScriptableCreate(ScriptableCreate):
        def __init__(self):
            ScriptableCreate.__init__(self, TEMPLATE_ROOT, MACRO_ROOT, SERVER_VERSION)

        def _create_query_data(self) -> dict:
            return QUERY_DATA


class TestScriptableDelete(ScriptableTestBase, unittest.TestCase):
    @property
    def class_for_test(self) -> Type[ScriptableBase]:
        return self._MockScriptableDelete

    @property
    def expected_template(self) -> str:
        return 'delete.sql'

    @property
    def script_lambda(self):
        return lambda obj: obj.delete_script()

    class _MockScriptableDelete(ScriptableDelete):
        def __init__(self):
            ScriptableDelete.__init__(self, TEMPLATE_ROOT, MACRO_ROOT, SERVER_VERSION)

        def _delete_query_data(self) -> dict:
            return QUERY_DATA


class TestScriptableUpdate(ScriptableTestBase, unittest.TestCase):
    @property
    def class_for_test(self) -> Type[ScriptableBase]:
        return self._MockScriptableUpdate

    @property
    def expected_template(self) -> str:
        return 'update.sql'

    @property
    def script_lambda(self):
        return lambda obj: obj.update_script()

    class _MockScriptableUpdate(ScriptableUpdate):
        def __init__(self):
            ScriptableUpdate.__init__(self, TEMPLATE_ROOT, MACRO_ROOT, SERVER_VERSION)

        def _update_query_data(self) -> dict:
            return QUERY_DATA
