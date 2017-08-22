# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsmo import Server


def find_schema(server: Server, metadata):
    """ Find the schema in the server to script as """
    schema_name = metadata.name if metadata.metadata_type_name == "Schema" else metadata.schema
    database = server.maintenance_db
    parent_schema = None
    try:
        if database.schemas is not None:
            parent_schema = database.schemas[schema_name]
            if parent_schema is not None:
                return parent_schema

        return None
    except Exception:
        return None


def find_table(server: Server, metadata):
    """ Find the table in the server to script as """
    return find_schema_child_object(server, 'tables', metadata)


def find_function(server: Server, metadata):
    """ Find the function in the server to script as """
    return find_schema_child_object(server, 'functions', metadata)


def find_database(server: Server, metadata):
    """ Find a database in the server """
    try:
        database_name = metadata.name
        database = server.databases[database_name]
        return database
    except Exception:
        return None


def find_view(server: Server, metadata):
    """ Find a view in the server """
    return find_schema_child_object(server, 'views', metadata)


def find_role(server: Server, metadata):
    """ Find a role in the server """
    try:
        role_name = metadata.name
        role = server.roles[role_name]
        return role
    except Exception:
        return None


def find_sequence(server: Server, metadata):
    """ Find a sequence in the server """
    return find_schema_child_object(server, 'sequences', metadata)


def find_datatype(server: Server, metadata):
    """ Find a datatype in the server """
    return find_schema_child_object(server, 'datatypes', metadata)


def find_schema_child_object(server, prop_name: str, metadata):
    """
    Find an object that is a child of a schema object.
    :param prop_name: name of the property used to query for objects
    of this type on the schema
    :param metadata: metadata including object name and schema name
    """
    try:
        obj_name = metadata.name
        parent_schema = find_schema(server, metadata)
        if not parent_schema:
            return None
        obj_collection = getattr(parent_schema, prop_name)
        if not obj_collection:
            return None
        obj = obj_collection[obj_name]
        return obj
    except Exception:
        return None


def get_object(server: Server, object_type: str, metadata):
    """ Retrieve a given object """
    object_map = {
        "Table": find_table,
        "Schema": find_schema,
        "Database": find_database,
        "View": find_view,
        "Role": find_role,
        "Function": find_function,
        "Sequence": find_sequence,
        "DataType": find_datatype
    }
    return object_map[object_type](server, metadata)
