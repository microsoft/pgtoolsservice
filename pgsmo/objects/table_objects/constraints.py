# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta

import pgsmo.objects.node_object as node
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Constraint(node.NodeObject, metaclass=ABCMeta):
    """Base class for constraints. Provides basic properties for all constraints"""

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: node.NodeObject, **kwargs) -> 'Constraint':
        """
        Creates a constraint from the results of a node query for any constraint
        :param server: Server that owns the constraint
        :param parent: Parent object of the constraint. Should be Table/View
        :param kwargs: A row from a constraint nodes query
        Kwargs:
            name str: Name of the constraint
            oid int: Object ID of the constraint
            convalidated bool: ? TODO: Figure out what this value means
        :return: An instance of a constraint
        """
        constraint = cls(server, parent, kwargs['name'])
        constraint._oid = kwargs['oid']
        constraint._convalidated = kwargs['convalidated']

        return constraint

    def __init__(self, server: 's.Server', parent: node.NodeObject, name: str):
        super(Constraint, self).__init__(server, parent, name)

        # Declare constraint-specific basic properties
        self._convalidated = None

    # PROPERTIES ###########################################################
    @property
    def convalidated(self):
        return self._convalidated

    # IMPLEMENTATION DETAILS ###############################################
    def get_template_vars(self):
        template_vars = {'oid': self.oid}
        return template_vars

class CheckConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_check')

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT


class ExclusionConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_exclusion')

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT


class ForeignKeyConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_fk')

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT


class IndexConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_index')

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT