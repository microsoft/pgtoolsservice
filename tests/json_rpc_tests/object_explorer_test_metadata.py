# Loop through the dictionary and then create the objects
# Fire objectexplorer/createsession request
# Check the root node
# Loop through the individual objects and objectexplorer/expand request for each of the object
# Get the object metadata for the expanded object and then expand on the children if present
# Repeat this until you reach a leaf node


import uuid


def _name():
    return uuid.uuid4().hex


def _display_name_template_for_database_objects():
    return 'public.{0}'


def _display_name_template_for_columns():
    return '{0} (int4)'  # Todo parameterize the datatype


def _display_name_template_for_constraints():
    return '{0} (Unique, Non-Clustered)'  # Todo parameterize index type


TABLE_METADATA: dict = {
    'Columns': {'Name': _name(), 'DisplayName': _display_name_template_for_columns()},
    'Constraints': {'Name': _name()},
    'Indexes': {'Name': _name(), 'DisplayName': _display_name_template_for_constraints()},
    'Rules': {'Name': _name()},
    'Triggers': {'Name': _name()}
}

DATABASE_METADATA: dict = {
    'Tables': {'Children': TABLE_METADATA, 'Name': uuid.uuid4().hex, 'DisplayName': _display_name_template_for_database_objects()},
    'Views': {},
    'Functions': {},
    'Collations': {},
    'Data Types': {},
    'Sequences': {},
    'Schemas': {},
    'Extensions': {},
    'Materialized Views': {}
}

META_DATA: dict = {
    'Databases': {'Children': DATABASE_METADATA, 'Name': uuid.uuid4().hex},
    'System Databases': {},
    'Roles': {},
    'Tablespaces': {}
}

CREATE_SCRIPTS: dict = {
    'Databases': 'CREATE DATABASE "{Databases_Name}"',
    'Tables': 'CREATE TABLE PUBLIC."{Tables_Name}" ();',
    'Columns': 'ALTER TABLE PUBLIC."{Tables_Name}" ADD COLUMN "{Columns_Name}" INTEGER;',
    'Constraints': 'ALTER TABLE PUBLIC."{Tables_Name}" ADD CONSTRAINT "{Constraints_Name}" CHECK("{Columns_Name}" < 5);',
    'Indexes': 'CREATE UNIQUE INDEX "{Indexes_Name}" ON PUBLIC."{Tables_Name}" ("{Columns_Name}");',
    'Rules': 'CREATE RULE "{Rules_Name}" AS ON UPDATE TO PUBLIC."{Tables_Name}" DO ALSO NOTIFY "{Tables_Name}";'
}

GET_OID_SCRIPTS: dict = {
    'Databases': "SELECT oid from pg_database where datname = '{Databases_Name}';",
    'Tables': "SELECT * FROM pg_attribute WHERE attrelid = '{Tables_Name}'::regclass;"
}
