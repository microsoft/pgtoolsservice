# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""A module that handles autocompletion metadata querying and
initialization of the completion object."""

import os
import threading
from collections import OrderedDict
from logging import Logger
from typing import Any, Callable

from prompt_toolkit.completion import Completer

from ossdbtoolsservice.connection import PooledConnection
from ossdbtoolsservice.language.completion import PGCompleter
from ossdbtoolsservice.language.metadata_executor import MetadataExecutor
from pgsmo import Server as PGServer


class CompletionRefresher:
    """
    Handles creating a PGCompleter object and populates it with the relevant
    completion suggestions in a background thread.
    """

    refreshers: dict = OrderedDict()

    def __init__(
        self,
        pooled_connection: PooledConnection,
        logger: Logger | None = None,
        completer_type: type[Completer] | None = None,
    ) -> None:
        self.pooled_connection = pooled_connection
        self.logger: Logger | None = logger
        self.completer_type = completer_type or PGCompleter
        self._server: PGServer | None = None
        self._completer_thread: threading.Thread | None = None
        self._restart_refresh: threading.Event = threading.Event()

    def refresh(
        self,
        callbacks: Callable[[PGCompleter], None] | list[Callable[[PGCompleter], None]],
        history: list[str] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> str:
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
            return "Auto-completion refresh restarted."
        else:
            self._completer_thread = threading.Thread(
                target=self._bg_refresh,
                args=(callbacks, history, settings),
                name="completion_refresh",
            )
            self._completer_thread.daemon = True
            self._completer_thread.start()
            return "Auto-completion refresh started in the background."  # TODO localize

    def is_refreshing(self) -> None | bool:
        return self._completer_thread is not None and self._completer_thread.is_alive()

    def _bg_refresh(
        self,
        callbacks: Callable[[PGCompleter], None] | list[Callable[[PGCompleter], None]],
        history: list[str] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> None:
        settings = settings or {}
        completer = self.completer_type(smart_completion=True, settings=settings)

        with self.pooled_connection as connection:
            server = PGServer(connection)
            server.refresh()
            metadata_executor = MetadataExecutor(server)

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
                        # Break out of while loop if the for loop finishes naturally
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
                    self.logger.exception("Error during metadata refresh: %s", e)

            for callback in callbacks:
                callback(completer)

            if self._restart_refresh.is_set():
                self._restart_refresh.clear()


def refresher(
    name: str, refreshers: dict = CompletionRefresher.refreshers
) -> Callable[..., Any]:
    """Decorator to populate the dictionary of refreshers with the current
    function.
    """

    def wrapper(wrapped: Callable) -> Any:
        refreshers[name] = wrapped
        return wrapped

    return wrapper


@refresher("schemata")
def refresh_schemata(completer: PGCompleter, metadata_executor: MetadataExecutor) -> None:
    completer.set_search_path(metadata_executor.search_path())
    completer.extend_schemata(metadata_executor.schemata())


@refresher("tables")
def refresh_tables(completer: PGCompleter, metadata_executor: MetadataExecutor) -> None:
    completer.extend_relations(metadata_executor.tables(), kind="tables")
    completer.extend_columns(metadata_executor.table_columns(), kind="tables")
    completer.extend_foreignkeys(metadata_executor.foreignkeys())


@refresher("views")
def refresh_views(completer: PGCompleter, metadata_executor: MetadataExecutor) -> None:
    completer.extend_relations(metadata_executor.views(), kind="views")
    completer.extend_columns(metadata_executor.view_columns(), kind="views")


@refresher("types")
def refresh_types(completer: PGCompleter, metadata_executor: MetadataExecutor) -> None:
    completer.extend_datatypes(metadata_executor.datatypes())


@refresher("databases")
def refresh_databases(completer: PGCompleter, metadata_executor: MetadataExecutor) -> None:
    completer.extend_database_names(metadata_executor.databases())


@refresher("casing")
def refresh_casing(completer: PGCompleter, metadata_executor: MetadataExecutor) -> None:
    casing_file = completer.casing_file
    if not casing_file:
        return
    generate_casing_file = completer.generate_casing_file
    if generate_casing_file and not os.path.isfile(casing_file):
        casing_prefs = "\n".join(str(c) for c in metadata_executor.casing())
        with open(casing_file, "w") as f:
            f.write(casing_prefs)
    if os.path.isfile(casing_file):
        with open(casing_file) as f:
            completer.extend_casing([line.strip() for line in f])


@refresher("functions")
def refresh_functions(completer: PGCompleter, metadata_executor: MetadataExecutor) -> None:
    completer.extend_functions(metadata_executor.functions())
