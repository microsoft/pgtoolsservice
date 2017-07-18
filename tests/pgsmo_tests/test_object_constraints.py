# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta
import unittest

from pgsmo.objects.table_objects.constraints import (
    CheckConstraint, ExclusionConstraint, ForeignKeyConstraint, IndexConstraint
)
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class ConstraintTestBase(NodeObjectTestBase, metaclass=ABCMeta):
    NODE_ROW = {
        'convalidated': True,
        'name': 'constraint',
        'oid': 123
    }

    @property
    def basic_properties(self):
        return {
            '_convalidated': ConstraintTestBase.NODE_ROW['convalidated'],
            'convalidated': ConstraintTestBase.NODE_ROW['convalidated']
        }

    @property
    def collections(self):
        return []

    @property
    def node_query(self) -> dict:
        return ConstraintTestBase.NODE_ROW


class TestCheckConstraint(ConstraintTestBase, unittest.TestCase):
    @property
    def class_for_test(self):
        return CheckConstraint


class TestExclusionConstraint(ConstraintTestBase, unittest.TestCase):
    @property
    def class_for_test(self):
        return ExclusionConstraint


class TestForeignKeyConstraint(ConstraintTestBase, unittest.TestCase):
    @property
    def class_for_test(self):
        return ForeignKeyConstraint


class TestIndexConstraint(ConstraintTestBase, unittest.TestCase):
    @property
    def class_for_test(self):
        return IndexConstraint
