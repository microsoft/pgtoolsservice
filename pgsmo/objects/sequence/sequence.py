# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsmo.objects.node_object import NodeObject, get_nodes
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')


class Sequence(NodeObject):
    @classmethod
    def get_nodes_for_parent(cls, conn: querying.ServerConnection, schema_id: int) -> List['Sequence']:
        """
        Generates a list of sequences for a given schema.
        :param conn: Connection to use to lookup the sequences for a schema
        :param schema_id: Object ID of the schema to retrieve sequences for
        :return: List of Sequence objects
        """
        return get_nodes(conn, TEMPLATE_ROOT, cls._from_node_query, scid=schema_id)

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'Sequence':
        """
        Creates a Sequence object from the result of a sequence node query
        :param conn: Connection that executed the node query
        :param kwargs: Row from a sequence node query
        Kwargs:
            oid int: Object ID of the sequence
            name str: Name of the sequence
        :return: A Sequence instance
        """
        seq = cls(conn, kwargs['name'])
        seq._oid = kwargs['oid']

        return seq

    def __init__(self, conn: querying.ServerConnection, name: str):
        super(Sequence, self).__init__(conn, name)
