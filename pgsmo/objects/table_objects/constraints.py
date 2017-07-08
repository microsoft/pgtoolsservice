# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta, abstractmethod
from typing import List, Optional

import pgsmo.objects.node_object as node
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


class Constraint(node.NodeObject, metaclass=ABCMeta):
    @classmethod
    def get_nodes_for_parent(cls, conn: querying.ServerConnection, tid: int) -> List['Constraint']:
        return node.get_nodes(conn, cls._template_path(), cls._from_node_query, tid=tid)

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'Constraint':
        constraint = cls(conn, kwargs['name'])
        constraint._oid = kwargs['oid']
        constraint._convalidated = kwargs['convalidated']

        return constraint

    def __init__(self, conn: querying.ServerConnection, name: str):
        super(Constraint, self).__init__(conn, name)

        # Declare constraint-specific basic properties
        self._convalidated = None

    # PROPERTIES ###########################################################
    @classmethod
    @abstractmethod
    def _template_path(cls) -> str:
        pass

    @property
    def convalidated(self):
        return self._convalidated


class CheckConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_check')

    @classmethod
    def _template_path(cls) -> str:
        return cls.TEMPLATE_ROOT


class ExclusionConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_exclusion')

    @classmethod
    def _template_path(cls) -> str:
        return cls.TEMPLATE_ROOT


class ForeignKeyConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_fk')

    @classmethod
    def _template_path(cls) -> str:
        return cls.TEMPLATE_ROOT


class IndexConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_index')

    @classmethod
    def _template_path(cls) -> str:
        return cls.TEMPLATE_ROOT
