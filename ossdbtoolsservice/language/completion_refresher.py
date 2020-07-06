# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""A module that handles autocompletion metadata querying and initialization of the completion object."""

import threading
from logging import Logger  # noqa
import os
from collections import OrderedDict

from pgsmo import Server as PGServer
from mysqlsmo import Server as MySQLServer
from ossdbtoolsservice.driver import ServerConnection
from ossdbtoolsservice.language.completion import PGCompleter, MySQLCompleter
from ossdbtoolsservice.language.metadata_executor import MetadataExecutor
from ossdbtoolsservice.utils.constants import PG_PROVIDER_NAME, MYSQL_PROVIDER_NAME

COMPLETER_MAP = {
    PG_PROVIDER_NAME: PGCompleter,
    MYSQL_PROVIDER_NAME: MySQLCompleter
}

SERVER_MAP = {
    PG_PROVIDER_NAME: PGServer,
    MYSQL_PROVIDER_NAME: MySQLServer
}

class CompletionRefresher:
    """
    Handles creating a PGCompleter object and populates it with the relevant
    completion suggestions in a background thread.
    """

    refreshers = OrderedDict()

    def __init__(self, connection: ServerConnection, logger: Logger = None):
        self.connection = connection
        self.logger: Logger = logger
        self.server: 'Server' = None
        self._completer_thread: threading.Thread = None
        self._restart_refresh: threading.Event = threading.Event()

    def refresh(self, callbacks, history=None, settings=None) -> str:
        """
        Creates a PGCompleter object and populates it with the relevant
        completion suggestions in a background thread.

        settings - dict of settings for completer object
        callbacks - A function or a list of functions to call after the thread
                    has completed the refresh. The newly created completion
                    object will be passed in as an argument to each callback.
        """
        if self.server is None:
            # Delay server creation until on background thread
            self.server = SERVER_MAP[self.connection._provider_name](self.connection)

        if self.is_refreshing():
            self._restart_refresh.set()
            return 'Auto-completion refresh restarted.'
        else:
            self._completer_thread = threading.Thread(
                target=self._bg_refresh,
                args=(callbacks, history, settings),
                name='completion_refresh')
            self._completer_thread.daemon = True
            self._completer_thread.start()
            return 'Auto-completion refresh started in the background.'     # TODO localize

    def is_refreshing(self):
        return self._completer_thread and self._completer_thread.is_alive()

    def _bg_refresh(self, callbacks, history=None, settings=None):
        settings = settings or {}
        completer: 'Completer' = COMPLETER_MAP[self.connection._provider_name](smart_completion=True, settings=settings)

        self.server.refresh()
        metadata_executor = MetadataExecutor(self.server)

        # If callbacks is a single function then push it into a list.
        if callable(callbacks):
            callbacks = [callbacks]

        try:
            while True:
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

            # Load history into completer so it can learn user preferences
            n_recent = 100
            if history:
                for recent in history[-n_recent:]:
                    completer.extend_query_history(recent, is_init=True)

        except Exception as e:
            if self.logger:
                self.logger.exception('Error during metadata refresh: {0}', e)

        for callback in callbacks:
            callback(completer)

        if self._restart_refresh.is_set():
            self._restart_refresh.clear()


def refresher(name, refreshers=CompletionRefresher.refreshers):
    """Decorator to populate the dictionary of refreshers with the current
    function.
    """
    def wrapper(wrapped):
        refreshers[name] = wrapped
        return wrapped
    return wrapper


@refresher('schemata')
def refresh_schemata(completer: 'Completer', metadata_executor: MetadataExecutor):
    completer.set_search_path(metadata_executor.search_path())
    completer.extend_schemata(metadata_executor.schemata())


@refresher('tables')
def refresh_tables(completer: 'Completer', metadata_executor: MetadataExecutor):
    completer.extend_relations(metadata_executor.tables(), kind='tables')
    completer.extend_columns(metadata_executor.table_columns(), kind='tables')
    completer.extend_foreignkeys(metadata_executor.foreignkeys())


@refresher('views')
def refresh_views(completer: 'Completer', metadata_executor: MetadataExecutor):
    completer.extend_relations(metadata_executor.views(), kind='views')
    completer.extend_columns(metadata_executor.view_columns(), kind='views')


@refresher('types')
def refresh_types(completer: 'Completer', metadata_executor: MetadataExecutor):
    completer.extend_datatypes(metadata_executor.datatypes())


@refresher('databases')
def refresh_databases(completer: 'Completer', metadata_executor: MetadataExecutor):
    completer.extend_database_names(metadata_executor.databases())


@refresher('casing')
def refresh_casing(completer: 'Completer', metadata_executor: MetadataExecutor):
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
def refresh_functions(completer: 'Completer', metadata_executor: MetadataExecutor):
    completer.extend_functions(metadata_executor.functions())
