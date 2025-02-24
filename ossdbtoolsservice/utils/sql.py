from psycopg import sql


def as_sql(query: str) -> sql.SQL:
    """
    Convert a string to a psycopg.sql.SQL object.

    Pylance reports a "reportArgumentType" error when
    strings are not Literals. This consolidates the
    # type:ignore to one place.
    """
    return sql.SQL(query)  # type: ignore
