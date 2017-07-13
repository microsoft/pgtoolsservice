# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta

import pgsmo.objects.node_object as node
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


class Constraint(node.NodeObject, metaclass=ABCMeta):
    """Base class for constraints. Provides basic properties for all constraints"""

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'Constraint':
        """
        Creates a constraint from the results of a node query for any constraint
        :param conn: The connection used to execute the nodes query
        :param kwargs: A row from a constraint nodes query
        Kwargs:
            name str: Name of the constraint
            oid int: Object ID of the constraint
            convalidated bool: ? TODO: Figure out what this value means
        :return: An instance of a constraint
        """
        constraint = cls(conn, kwargs['name'])
        constraint._oid = kwargs['oid']
        constraint._convalidated = kwargs['convalidated']

        return constraint

    def __init__(self, conn: querying.ServerConnection, name: str):
        super(Constraint, self).__init__(conn, name)

        # Declare constraint-specific basic properties
        self._convalidated = None

    # PROPERTIES ###########################################################
    @property
    def convalidated(self):
        return self._convalidated


class CheckConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_check')

    @classmethod
    def _template_root(cls, conn: querying.ServerConnection) -> str:
        return cls.TEMPLATE_ROOT


class ExclusionConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_exclusion')

    @classmethod
    def _template_root(cls, conn: querying.ServerConnection) -> str:
        return cls.TEMPLATE_ROOT


class ForeignKeyConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_fk')

    @classmethod
    def _template_root(cls, conn: querying.ServerConnection) -> str:
        return cls.TEMPLATE_ROOT


class IndexConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_index')

    @classmethod
    def _template_root(cls, conn: querying.ServerConnection) -> str:
        return cls.TEMPLATE_ROOT
