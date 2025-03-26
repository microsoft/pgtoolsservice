# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from abc import ABCMeta

from pgsmo.objects.table_objects.constraints import (
    CheckConstraint,
    ExclusionConstraint,
    ForeignKeyConstraint,
    IndexConstraint,
)
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class ConstraintTestBase(NodeObjectTestBase, metaclass=ABCMeta):
    NODE_ROW = {"convalidated": True, "name": "constraint", "oid": 123}

    @property
    def basic_properties(self):
        return {
            "_convalidated": ConstraintTestBase.NODE_ROW["convalidated"],
            "convalidated": ConstraintTestBase.NODE_ROW["convalidated"],
        }

    @property
    def collections(self):
        return []

    @property
    def node_query(self) -> dict:
        return ConstraintTestBase.NODE_ROW


class TestCheckConstraint(ConstraintTestBase, unittest.TestCase):
    @property
    def full_properties(self):
        return {
            "name": "name",
            "comment": "comment",
            "src": "src",
            "no_inherit": "no_inherit",
        }

    @property
    def property_query(self):
        return {"name": "test", "comment": "test_comment", "src": "test", "no_inherit": True}

    @property
    def class_for_test(self):
        return CheckConstraint


class TestExclusionConstraint(ConstraintTestBase, unittest.TestCase):
    @property
    def full_properties(self):
        return {
            "comment": "comment",
            "amname": "amname",
            "columns": "columns",
            "fillfactor": "fillfactor",
            "spcname": "spcname",
            "deferrable": "deferrable",
            "deferred": "deferred",
            "constraint": "constraint",
            "cascade": "cascade",
        }

    @property
    def property_query(self):
        return {
            "comment": "test_comment",
            "amname": "test",
            "columns": "test",
            "fillfactor": "test",
            "spcname": "test",
            "deferrable": True,
            "deferred": True,
            "constraint": "test",
            "cascade": True,
        }

    @property
    def class_for_test(self):
        return ExclusionConstraint


class TestForeignKeyConstraint(ConstraintTestBase, unittest.TestCase):
    @property
    def full_properties(self):
        return {
            "name": "name",
            "comment": "comment",
            "columns": "columns",
            "remote_schema": "remote_schema",
            "remote_table": "remote_table",
            "fmatchtype": "fmatchtype",
            "fupdtype": "fupdtype",
            "fdeltype": "fdeltype",
            "deferrable": "deferrable",
            "deferred": "deferred",
            "cascade": "cascade",
        }

    @property
    def property_query(self):
        return {
            "name": "test",
            "comment": "test",
            "columns": "test",
            "remote_schema": "test",
            "remote_table": "test",
            "fmatchtype": True,
            "fupdtype": "c",
            "fdeltype": "c",
            "deferrable": True,
            "deferred": True,
            "cascade": True,
        }

    @property
    def class_for_test(self):
        return ForeignKeyConstraint


class TestIndexConstraint(ConstraintTestBase, unittest.TestCase):
    @property
    def full_properties(self):
        return {
            "name": "name",
            "comment": "comment",
            "index": "index",
            "fillfactor": "fillfactor",
            "spcname": "spcname",
            "deferrable": "deferrable",
            "deferred": "deferred",
            "cascade": "cascade",
        }

    @property
    def property_query(self):
        return {
            "name": "test",
            "comment": "test",
            "index": "test",
            "fillfactor": "test",
            "spcname": "test",
            "deferrable": True,
            "deferred": True,
            "cascade": True,
        }

    @property
    def class_for_test(self):
        return IndexConstraint
