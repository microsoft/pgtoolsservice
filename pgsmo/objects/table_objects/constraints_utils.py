from pgsmo.objects.server import server as s  # noqa
import smo.utils.templating as templating

GET_INDEX_CONSTRAINT_TEMPLATE_ROOT = templating.get_template_root(
    __file__, "constraint_index"
)
GET_FOREIGN_CONSTRAINT_TEMPLATE_ROOT = templating.get_template_root(__file__, "constraint_fk")
GET_CHECK_CONSTRAINT_TEMPLATE_ROOT = templating.get_template_root(
    __file__, "constraint_check"
)
GET_EXCLUSION_CONSTRAINT_TEMPLATE_ROOT = templating.get_template_root(
    __file__, "constraint_exclusion"
)


def get_index_constraints(server, did, tid, ctype, cid=None) -> dict:
    server_version = server.connection.server_version

    sql = templating.render_template(
        templating.get_template_path(
            GET_INDEX_CONSTRAINT_TEMPLATE_ROOT, "properties.sql", server_version
        ),
        macro_roots=None,
        did=did,
        tid=tid,
        cid=cid,
        constraint_type=ctype,
    )

    result = server.connection.execute_dict(sql)

    for idx_cons in result[1]:
        sql = templating.render_template(
            templating.get_template_path(
                GET_INDEX_CONSTRAINT_TEMPLATE_ROOT, "get_constraint_cols.sql", server_version
            ),
            macro_roots=None,
            cid=idx_cons["oid"],
            colcnt=idx_cons["col_count"],
        )

        constraint_cols = server.connection.execute_dict(sql)

        columns = []
        for r in constraint_cols[1]:
            columns.append({"column": r["column"].strip('"')})

        idx_cons["columns"] = columns

        # INCLUDE clause in index is supported from PG-11+
        if server_version[0] >= 11:
            sql = templating.render_template(
                templating.get_template_path(
                    GET_INDEX_CONSTRAINT_TEMPLATE_ROOT,
                    "get_constraint_include.sql",
                    server_version,
                ),
                macro_roots=None,
                cid=idx_cons["oid"],
            )
            constraint_cols = server.connection.execute_dict(sql)

            idx_cons["include"] = [col["colname"] for col in constraint_cols[1]]

    return result[1]


def get_foreign_keys(server, tid, fkid=None):
    server_version = server.connection.server_version

    sql = templating.render_template(
        templating.get_template_path(
            GET_FOREIGN_CONSTRAINT_TEMPLATE_ROOT, "properties.sql", server_version
        ),
        macro_roots=None,
        tid=tid,
        cid=fkid,
    )

    result = server.connection.execute_dict(sql)

    for fk in result[1]:
        sql = templating.render_template(
            templating.get_template_path(
                GET_FOREIGN_CONSTRAINT_TEMPLATE_ROOT,
                "get_constraint_cols.sql",
                server_version,
            ),
            macro_roots=None,
            tid=tid,
            keys=zip(fk["confkey"], fk["conkey"]),
            confrelid=fk["confrelid"],
        )

        res = server.connection.execute_dict(sql)

        columns = []
        cols = []
        for row in res[1]:
            columns.append(
                {
                    "local_column": row["conattname"],
                    "references": fk["confrelid"],
                    "referenced": row["confattname"],
                    "references_table_name": fk["refnsp"] + "." + fk["reftab"],
                }
            )
            cols.append(row["conattname"])

        fk["columns"] = columns

        if not fkid:
            schema, table = get_parent(server, fk["columns"][0]["references"])
            fk["remote_schema"] = schema
            fk["remote_table"] = table

        coveringindex = search_coveringindex(server, tid, cols)
        fk["coveringindex"] = coveringindex
        if coveringindex:
            fk["autoindex"] = False
            fk["hasindex"] = True
        else:
            fk["autoindex"] = True
            fk["hasindex"] = False

    return result[1]


def get_check_constraints(server, tid):
    server_version = server.connection.server_version

    sql = templating.render_template(
        templating.get_template_path(
            GET_CHECK_CONSTRAINT_TEMPLATE_ROOT, "properties.sql", server_version
        ),
        macro_roots=None,
        tid=tid,
    )

    result = server.connection.execute_dict(sql)

    return result[1]


def get_exclusion_constraints(server, did, tid):
    server_version = server.connection.server_version

    sql = templating.render_template(
        templating.get_template_path(
            GET_EXCLUSION_CONSTRAINT_TEMPLATE_ROOT, "properties.sql", server_version
        ),
        macro_roots=None,
        did=did,
        tid=tid,
    )

    result = server.connection.execute_dict(sql)

    for ex in result[1]:
        sql = templating.render_template(
            templating.get_template_path(
                GET_EXCLUSION_CONSTRAINT_TEMPLATE_ROOT,
                "get_constraint_cols.sql",
                server_version,
            ),
            macro_roots=None,
            cid=ex["oid"],
            colcnt=ex["col_count"],
        )
        res = server.connection.execute_dict(sql)

        columns = _get_columns(res)
        ex["columns"] = columns

        # INCLUDE clause in index is supported from PG-11+
        if server_version[0] >= 11:
            sql = templating.render_template(
                templating.get_template_path(
                    GET_EXCLUSION_CONSTRAINT_TEMPLATE_ROOT,
                    "get_constraint_include.sql",
                    server_version,
                ),
                macro_roots=None,
                cid=ex["oid"],
            )
            res = server.connection.execute_dict(sql)

            ex["include"] = [col["colname"] for col in res[1]]

        if ex.get("amname", "") == "":
            ex["amname"] = "btree"

    return result[1]


def get_parent(server, tid, template_path=None):
    server_version = server.connection.server_version

    sql = templating.render_template(
        templating.get_template_path(
            GET_FOREIGN_CONSTRAINT_TEMPLATE_ROOT, "get_parent.sql", server_version
        ),
        macro_roots=None,
        tid=tid,
    )

    rset = server.connection.execute_2darray(sql)

    schema = ""
    table = ""
    if "rows" in rset and len(rset["rows"]) > 0:
        schema = rset["rows"][0][0]
        table = rset["rows"][0][1]

    return schema, table


def search_coveringindex(server, tid, cols):
    cols = set(cols)
    server_version = server.connection.server_version

    sql = templating.render_template(
        templating.get_template_path(
            GET_FOREIGN_CONSTRAINT_TEMPLATE_ROOT, "get_constraints.sql", server_version
        ),
        macro_roots=None,
        tid=tid,
    )

    constraints = server.connection.execute_dict(sql)

    for constraint in constraints[1]:
        sql = templating.render_template(
            templating.get_template_path(
                GET_FOREIGN_CONSTRAINT_TEMPLATE_ROOT, "get_cols.sql", server_version
            ),
            macro_roots=None,
            cid=constraint["oid"],
            colcnt=constraint["col_count"],
        )
        rest = server.connection.execute_dict(sql)

        index_cols = set()
        for r in rest[1]:
            index_cols.add(r["column"].strip('"'))

        if len(cols - index_cols) == len(index_cols - cols) == 0:
            return constraint["idxname"]

    return None


def _get_columns(res):
    #
    # pgAdmin 4 - PostgreSQL Tools
    #
    # Copyright (C) 2013 - 2017, The pgAdmin Development Team
    # This software is released under the PostgreSQL Licence
    #
    """
    Get columns form response and return in required format.
    :param res: response form constraints.
    :return: column list.
    """
    columns = []
    for row in res[1]:
        if row["options"] & 1:
            order = False
            nulls_order = bool(row["options"] & 2)
        else:
            order = True
            nulls_order = bool(row["options"] & 2)

        columns.append(
            {
                "column": row["coldef"].strip('"'),
                "oper_class": row["opcname"],
                "order": order,
                "nulls_order": nulls_order,
                "operator": row["oprname"],
                "col_type": row["datatype"],
                "is_exp": row["is_exp"],
            }
        )
    return columns
