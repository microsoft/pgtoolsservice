# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsmo import Server


def get_schema_from_db(schema_name, databases):
    try:
        schema = databases[schema_name]
        return schema
    except NameError:
        return None


def find_schema(server: Server, metadata):
    """ Find the schema in the server to script as """
    schema_name = metadata.name if metadata.metadata_type_name == "Schema" else metadata.schema
    databases = server.databases
    parent_schema = None
    try:
        for db in databases:
            if db.schemas is not None:
                parent_schema = get_schema_from_db(schema_name, db.schemas)
                if parent_schema is not None:
                    return parent_schema
    except Exception:
        return None


def find_table(server: Server, metadata):
    """ Find the table in the server to script as """
    try:
        table_name = metadata.name
        parent_schema = find_schema(server, metadata)
        for table in parent_schema.tables:
            return parent_schema.tables[table_name]
    except Exception:
        return None


def find_function(server: Server, metadata):
    """ Find the function in the server to script as """
    try:
        function_name = metadata.name
        parent_schema = find_schema(server, metadata)
        return parent_schema.functions[function_name]
    except Exception:
        return None


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
    try:
        view_name = metadata.name
        parent_schema = find_schema(server, metadata)
        view = parent_schema.views[view_name]
        return view
    except Exception:
        return None


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
    try:
        sequence_name = metadata.name
        sequence = server.sequences[sequence_name]
        return sequence
    except Exception:
        return None
