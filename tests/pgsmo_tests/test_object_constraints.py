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
    def full_properties(self):
        return {            
            "schema": "schema",
            "table": "table",
            "name": "name",
            "comment": "comment",
            "consrc": "consrc",
            "connoinherit": "connoinherit",
            "nspname": "nspname",
            "relname": "relname"
        }

    @property
    def property_query(self):
        return {
            "convalidated": True,  
            "schema": "test",
            "table": "test",
            "name": "test",
            "comment": "test_comment",
            "consrc": "test",
            "connoinherit": "test",
            "nspname": "test_nspname",
            "relname": "test_relname"
        }

    @property
    def class_for_test(self):
        return CheckConstraint


class TestExclusionConstraint(ConstraintTestBase, unittest.TestCase):

    @property
    def full_properties(self):
        return {            
            "name": "name",
            "schema": "schema",
            "table": "table",
            "comment": "comment",
            "amname": "amname",
            "columns": "columns",
            "fillfactor": "fillfactor",
            "spcname": "spcname",
            "condeferrable": "condeferrable",
            "condeferred": "condeferred",
            "constraint": "constraint",
            "cascade": "cascade"
        }

    @property
    def property_query(self):
        return {            
            "name": "test",
            "schema": "test",
            "table": "test",
            "comment": "test_comment",
            "amname": "test",
            "columns": "test",
            "fillfactor": "test",
            "spcname": "test",
            "condeferrable": "test",
            "condeferred": "test",
            "constraint": "test",
            "cascade": True
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
            "schema": "schema",
            "table": "table",
            "columns": "columns",
            "remote_schema": "remote_schema",
            "remote_table": "remote_table",
            "confmatchtype": "confmatchtype",
            "confupdtype": "confupdtype",
            "confdeltype": "confdeltype",
            "condeferrable": "condeferrable",
            "condeferred": "condeferred",
            "cascade": "cascade"
        }

    @property
    def property_query(self):
        return {
            "name": "test",
            "comment": "test",
            "schema": "test",
            "table": "test",
            "columns": "test",
            "remote_schema": "test",
            "remote_table": "test",
            "confmatchtype": "test",
            "confupdtype": "test",
            "confdeltype": "test",
            "condeferrable": "test",
            "condeferred": "test",
            "cascade": True
        }

    @property
    def class_for_test(self):
        return ForeignKeyConstraint


class TestIndexConstraint(ConstraintTestBase, unittest.TestCase):

    @property
    def full_properties(self):
        return {
            "name": "name",
            "schema": "schema",
            "table": "table",
            "comment": "comment",
            "index": "index",
            "fillfactor": "fillfactor",
            "spcname": "spcname",
            "condeferrable": "condeferrable",
            "condeferred": "condeferred",
            "cascade": "cascade"
        }

    @property
    def property_query(self):
        return {
            "name": "test",
            "schema": "test",
            "table": "test",
            "comment": "test",
            "index": "test",
            "fillfactor": "test",
            "spcname": "test",
            "condeferrable": "test",
            "condeferred": "test",
            "cascade": True
        }

    @property
    def class_for_test(self):
        return IndexConstraint
