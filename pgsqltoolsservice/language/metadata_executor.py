# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any, Dict, List, Tuple   # noqa

from pgsmo import Column, Database, Schema, Server, NodeCollection, Function, Table, View       # noqa
from pgsqltoolsservice.language.completion.packages.parseutils.meta import ColumnMetadata, ForeignKey, FunctionMetadata     # noqa


class MetadataExecutor(object):
    """
    Handles querying metadata from PGSMO and returning it in a form usable by the
    autocomplete code
    """

    def __init__(self, server: Server):
        self.server = server
        self.schemas: Dict[str, 'Schema'] = {}
        self.schemas_loaded = False
        self.all_tables = NodeCollection(lambda: self.populate_objects_under_schemas('tables'))
        self.all_views = NodeCollection(lambda: self.populate_objects_under_schemas('views'))

    def _load_schemas(self):
        database: Database = self.server.maintenance_db
        for schema in database.schemas:
            self.schemas[schema.name] = schema

    def _ensure_schemas_loaded(self):
        if not self.schemas_loaded:
            self._load_schemas()
            self.schemas_loaded = True

    @property
    def _schema_names(self) -> List[str]:
        self._ensure_schemas_loaded()
        return list(self.schemas.keys())

    def schemata(self) -> List[str]:
        return self._schema_names

    def search_path(self) -> List[str]:
        return list(self.server.search_path)

    def databases(self) -> List[str]:
        return list(map(lambda d: d.name, self.server.databases))

    def tables(self) -> List[tuple]:
        """return a 2-tuple of [schema,name]"""
        return list(map(lambda t: tuple([t.schema, t.name]), self.all_tables))

    def table_columns(self) -> List[tuple]:
        """return a 3-tuple of [schema,table,name]"""
        columns = []
        for table in self.all_tables:
            cols = map(lambda c, t=table: self._create_column_metadata(t.schema, t.name, c), table.columns)
            columns.extend(cols)
        return columns

    def foreignkeys(self) -> List[tuple]:
        # TODO Implement FK support. This requires adding properties to the ForeignKeyConstraint class
        return []

    def views(self) -> List[tuple]:
        """return a 2-tuple of [schema,name]"""
        return list(map(lambda v: tuple([v.parent.name, v.name]), self.all_views))

    def view_columns(self) -> List[tuple]:
        """return a 3-tuple of [schema,table,name]"""
        columns = []
        for view in self.all_views:
            cols = map(lambda c, v=view: self._create_column_metadata(v.schema, v.name, c), view.columns)
            columns.extend(cols)
        return columns

    def datatypes(self) -> List[tuple]:
        """return a 2-tuple of [schema,name]"""
        return list(map(lambda t: tuple([t.schema, t.name]), self.populate_objects_under_schemas('datatypes')))

    def casing(self) -> List[tuple]:
        # TODO Implement casing support.
        return []

    def functions(self) -> List[tuple]:
        # TODO Implement FK support. This requires adding properties to the ForeignKeyConstraint class
        func_metadatas: List[FunctionMetadata] = []
        funcs = self.populate_objects_under_schemas('functions')
        for f in funcs:
            function: Function = f
            # TODO investigate supporting arg_modes and proisagg.
            # TODO implement proretset in properties. It's defined as a prop but not actually implemented
            # Other tools use custom queries just for autocomplete, which is worth considering
            metadata = FunctionMetadata(function.schema, function.name, function.proargnames, f.proargtypenames, None,
                                        function.prorettypename, False, function.proiswindow, function.proretset, function.proargdefaultvals)
            func_metadatas.append(metadata)
        return func_metadatas

    # IMPLEMENTATION DETAILS ###############################################
    def _create_column_metadata(self, schema: str, parent: str, col: Column) -> Tuple:
        return tuple([schema, parent, col.name, col.datatype, col.has_default_value, col.defval])

    def populate_objects_under_schemas(self, obj_prop_name: str) -> List[Any]:
        """
        Returns list of tables or functions for all schemas

        Args:
            obj_prop_name: name of the property used to get the objects
        """
        self._ensure_schemas_loaded()
        objects = []
        for schema in self.schemas.values():
            object_matches: List[Any] = getattr(schema, obj_prop_name)
            objects.extend(object_matches)
        return objects
