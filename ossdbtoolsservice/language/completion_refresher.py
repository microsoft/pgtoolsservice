# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""A module that handles autocompletion metadata querying and initialization of the completion object."""

import threading
from logging import Logger  # noqa
import os
from collections import OrderedDict

from mysqlsmo import Server as MySQLServer
from ossdbtoolsservice.driver import ServerConnection
from ossdbtoolsservice.language.completion import MySQLCompleter
from ossdbtoolsservice.language.metadata_executor import MetadataExecutor
from ossdbtoolsservice.utils.constants import MYSQL_PROVIDER_NAME

COMPLETER_MAP = {
    MYSQL_PROVIDER_NAME: MySQLCompleter
}

SERVER_MAP = {
    MYSQL_PROVIDER_NAME: MySQLServer
}


class CompletionRefresher:
    """
    Handles creating a MYSQL object and populates it with the relevant
    completion suggestions in a background thread.
    """

    refreshers = {
        MYSQL_PROVIDER_NAME: OrderedDict()
    }

    def __init__(self, connection: ServerConnection, logger: Logger = None):
        self.connection = connection
        self.logger: Logger = logger
        self.server: MySQLServer = None
        self._completer_thread: threading.Thread = None
        self._restart_refresh: threading.Event = threading.Event()

    def refresh(self, callbacks, history=None, settings=None) -> str:
        """
        Creates a MYSQLCompleter object and populates it with the relevant
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
        completer: MySQLCompleter = COMPLETER_MAP[self.connection._provider_name](smart_completion=True, settings=settings)

        self.server.refresh()
        metadata_executor = MetadataExecutor(self.server)

        # If callbacks is a single function then push it into a list.
        if callable(callbacks):
            callbacks = [callbacks]

        try:
            while True:
                for do_refresh in self.refreshers[self.connection._provider_name].values():
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


def mysql_refresher(name, refreshers=CompletionRefresher.refreshers):
    """Decorator to populate the dictionary of refreshers with the current
    function.
    """
    def wrapper(wrapped):
        refreshers[MYSQL_PROVIDER_NAME][name] = wrapped
        return wrapped
    return wrapper


@mysql_refresher('schemata')
def mysql_refresh_schemata(completer, metadata_executor):
    # schemata - In MySQL Schema is the same as database. But for mycli
    # schemata will be the name of the current database.
    completer.extend_schemata(metadata_executor.server._maintenance_db_name)
    completer.set_dbname(metadata_executor.server._maintenance_db_name)


@mysql_refresher('functions')
def refresh_functions(completer: MySQLCompleter, metadata_executor: MetadataExecutor):
    completer.extend_functions(metadata_executor.functions())


@mysql_refresher('procedures')
def refresh_procedures(completer, metadata_executor):
    completer.extend_procedures(metadata_executor.procedures())


@mysql_refresher('tables')
def mysql_refresh_tables(completer, metadata_executor):
    if metadata_executor.server._maintenance_db_name:
        completer.extend_relations(metadata_executor.tables(), kind='tables')
        completer.extend_columns(metadata_executor.table_columns(), kind='tables')


@mysql_refresher('users')
def refresh_users(completer, metadata_executor):
    completer.extend_users(metadata_executor.users())


@mysql_refresher('show_commands')
def refresh_show_commands(completer, metadata_executor):
    completer.extend_show_items(metadata_executor.show_candidates())
