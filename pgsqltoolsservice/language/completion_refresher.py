# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""A module that handles autocompletion metadata querying and initialization of the completion object."""

from typing import Any, Dict, List, Tuple   # noqa
import threading
import os
from collections import OrderedDict

from pgsmo import Column, Database, Schema, Server, NodeCollection, Function, Table, View       # noqa
from pgsqltoolsservice.language.completion.packages.parseutils.meta import ColumnMetadata, ForeignKey, FunctionMetadata     # noqa
from pgsqltoolsservice.language.completion import PGCompleter


class CompletionRefresher(object):

    refreshers = OrderedDict()

    def __init__(self, server: Server):
        self.server = server
        self._completer_thread = None
        self._restart_refresh = threading.Event()

    def refresh(self, callbacks, history=None,
                settings=None):
        """
        Creates a PGCompleter object and populates it with the relevant
        completion suggestions in a background thread.

        settings - dict of settings for completer object
        callbacks - A function or a list of functions to call after the thread
                    has completed the refresh. The newly created completion
                    object will be passed in as an argument to each callback.
        """
        if self.is_refreshing():
            self._restart_refresh.set()
            return [(None, None, None, 'Auto-completion refresh restarted.')]
        else:
            self._completer_thread = threading.Thread(
                target=self._bg_refresh,
                args=(callbacks, history, settings),
                name='completion_refresh')
            self._completer_thread.setDaemon(True)
            self._completer_thread.start()
            return [(None, None, None,
                     'Auto-completion refresh started in the background.')]

    def is_refreshing(self):
        return self._completer_thread and self._completer_thread.is_alive()

    def _bg_refresh(self, callbacks, history=None, settings=None):
        settings = settings or {}
        completer = PGCompleter(smart_completion=True, settings=settings)

        self.server.refresh()
        metadata_executor = MetadataExecutor(self.server)

        # If callbacks is a single function then push it into a list.
        if callable(callbacks):
            callbacks = [callbacks]

        while 1:
            for do_refresh in self.refreshers.values():
                do_refresh(completer, metadata_executor)
                if self._restart_refresh.is_set():
                    self._restart_refresh.clear()
                    break
            else:
                # Break out of while loop if the for loop finishes natually
                # without hitting the break statement.
                break

            # Start over the refresh from the beginning if the for loop hit the
            # break statement.
            continue

        # Load history into pgcompleter so it can learn user preferences
        n_recent = 100
        if history:
            for recent in history[-n_recent:]:
                completer.extend_query_history(recent, is_init=True)

        for callback in callbacks:
            callback(completer)


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
        return list(map(lambda t: tuple(t.schema, t.name, self.all_tables)))

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
        return list(map(lambda v: tuple(v.parent.name, v.name, self.all_views)))

    def view_columns(self) -> List[tuple]:
        """return a 3-tuple of [schema,table,name]"""
        columns = []
        for view in self.all_views:
            cols = map(lambda c, v=view: self._create_column_metadata(v.schema, v.name, c), view.columns)
            columns.extend(cols)
        return columns

    def datatypes(self) -> List[tuple]:
        """return a 2-tuple of [schema,name]"""
        return list(map(lambda t: tuple(t.schema, t.name, self.populate_objects_under_schemas('datatypes'))))

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
        return tuple(schema, parent, col.name, col.datatype, col.has_default_value, col.defval)

    def populate_objects_under_schemas(self, obj_prop_name: str) -> List[Any]:
        """
        Returns list of tables or functions for all schemas

        Args:
            obj_prop_name: name of the property used to get the objects
        """
        self._ensure_schemas_loaded()
        objects = []
        for schema in self.schemas:
            object_matches: List[Any] = getattr(schema, obj_prop_name)
            objects.extend(object_matches)
        return objects


def refresher(name, refreshers=CompletionRefresher.refreshers):
    """Decorator to populate the dictionary of refreshers with the current
    function.
    """
    def wrapper(wrapped):
        refreshers[name] = wrapped
        return wrapped
    return wrapper


@refresher('schemata')
def refresh_schemata(completer: PGCompleter, metadata_executor: MetadataExecutor):
    completer.set_search_path(metadata_executor.search_path())
    completer.extend_schemata(metadata_executor.schemata())


@refresher('tables')
def refresh_tables(completer: PGCompleter, metadata_executor: MetadataExecutor):
    completer.extend_relations(metadata_executor.tables(), kind='tables')
    completer.extend_columns(metadata_executor.table_columns(), kind='tables')
    completer.extend_foreignkeys(metadata_executor.foreignkeys())


@refresher('views')
def refresh_views(completer: PGCompleter, metadata_executor: MetadataExecutor):
    completer.extend_relations(metadata_executor.views(), kind='views')
    completer.extend_columns(metadata_executor.view_columns(), kind='views')


@refresher('types')
def refresh_types(completer: PGCompleter, metadata_executor: MetadataExecutor):
    completer.extend_datatypes(metadata_executor.datatypes())


@refresher('databases')
def refresh_databases(completer: PGCompleter, metadata_executor: MetadataExecutor):
    completer.extend_database_names(metadata_executor.databases())


@refresher('casing')
def refresh_casing(completer: PGCompleter, metadata_executor: MetadataExecutor):
    casing_file = completer.casing_file
    if not casing_file:
        return
    generate_casing_file = completer.generate_casing_file
    if generate_casing_file and not os.path.isfile(casing_file):
        casing_prefs = '\n'.join(metadata_executor.casing())
        with open(casing_file, 'w') as f:
            f.write(casing_prefs)
    if os.path.isfile(casing_file):
        with open(casing_file, 'r') as f:
            completer.extend_casing([line.strip() for line in f])


@refresher('functions')
def refresh_functions(completer, metadata_executor: MetadataExecutor):
    completer.extend_functions(metadata_executor.functions())
