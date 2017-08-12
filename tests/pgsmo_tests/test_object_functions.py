# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta
import unittest

from pgsmo.objects.functions import Function, TriggerFunction
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class FunctionsTestBase(NodeObjectTestBase, metaclass=ABCMeta):
    NODE_ROW = {
        'name': 'funcname(arg1 int)',
        'oid': 123,
        'description': 'func description',
        'lanname': 'sql',
        'funcowner': 'postgres'
    }

    @property
    def basic_properties(self):
        return {
            'description': FunctionsTestBase.NODE_ROW['description'],
            '_description': FunctionsTestBase.NODE_ROW['description'],
            'language_name': FunctionsTestBase.NODE_ROW['lanname'],
            '_language_name': FunctionsTestBase.NODE_ROW['lanname'],
            'owner': FunctionsTestBase.NODE_ROW['funcowner'],
            '_owner': FunctionsTestBase.NODE_ROW['funcowner']
        }

    @property
    def full_properties(self):
        return {
            "arguments": "arguments",
            "proretset": "proretset",
            "prorettypename": "prorettypename",
            "procost": "procost",
            "provolatile": "provolatile",
            "proleakproof": "proleakproof",
            "proisstrict": "proisstrict",
            "prosecdef": "prosecdef",
            "proiswindow": "proiswindow",
            "proparallel": "proparallel",
            "prorows": "prorows",
            "variables": "variables",
            "probin": "probin",
            "prosrc_c": "prosrc_c",
            "prosrc": "prosrc",
            "func_args_without": "func_args_without",
            "acl": "acl",
            "seclabels": "seclabels"
        }

    @property
    def property_query(self) -> dict:
        return self.full_properties

    @property
    def collections(self):
        return []

    @property
    def node_query(self):
        return FunctionsTestBase.NODE_ROW


class TestFunction(FunctionsTestBase, unittest.TestCase):
    @property
    def class_for_test(self):
        return Function


class TestTriggerFunction(FunctionsTestBase, unittest.TestCase):
    @property
    def class_for_test(self):
        return TriggerFunction
