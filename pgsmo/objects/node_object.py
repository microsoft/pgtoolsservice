from typing import Optional

from pgsmo.utils.abstract_class_method import abstractclassmethod
import pgsmo.utils.templating as t
import pgsmo.utils.querying as q


class NodeObject:
    @abstractclassmethod
    def _from_node_query(cls, conn: q.ConnectionWrapper, **kwargs):
        pass

    def __init__(self, conn: q.ConnectionWrapper, name: str):
        # Define the state of the object
        self._conn: q.ConnectionWrapper = conn

        # Declare node basic properties
        self._name: str = name
        self._oid: Optional[int] = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def oid(self) -> Optional[int]:
        return self._oid

def get_nodes(conn: q.ConnectionWrapper, template_root: str, generator, **kwargs):
    sql = t.render_template(
        t.get_template_path(template_root, 'nodes.sql', conn.version),
        **kwargs
    )
    cols, rows = q.execute_dict(conn, sql)

    return [generator(**row) for row in rows]
