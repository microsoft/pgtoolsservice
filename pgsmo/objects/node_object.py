import pgsmo.utils.templating as t
import pgsmo.utils.querying as q


def get_nodes(conn: q.ConnectionWrapper, template_root: str, generator, **kwargs):
    sql = t.render_template(
        t.get_template_path(template_root, 'nodes.sql', conn.version),
        **kwargs
    )
    cols, rows = q.execute_dict(conn, sql)

    return [generator(**row) for row in rows]
