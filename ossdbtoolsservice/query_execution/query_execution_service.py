# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ntpath
import threading
import uuid
from datetime import datetime
from typing import Any, Callable, TypeVar

import psycopg
import psycopg.errors
import sqlparse

from ossdbtoolsservice.connection import (
    ConnectionService,
    PooledConnection,
)
from ossdbtoolsservice.connection.core.server_connection import ServerConnection
from ossdbtoolsservice.hosting import RequestContext, Service, ServiceProvider
from ossdbtoolsservice.query import (
    Batch,
    BatchEvents,
    ExecutionState,
    Query,
    QueryEvents,
    QueryExecutionSettings,
    ResultSetStorageType,
)
from ossdbtoolsservice.query import compute_selection_data_for_batches as compute_batches
from ossdbtoolsservice.query.contracts import (
    BatchSummary,
    SaveResultsRequestParams,
    SelectionData,
    SubsetResult,
)
from ossdbtoolsservice.query.data_storage import (
    FileStreamFactory,
    SaveAsCsvFileStreamFactory,
    SaveAsExcelFileStreamFactory,
    SaveAsJsonFileStreamFactory,
)
from ossdbtoolsservice.query_execution.contracts import (
    BATCH_COMPLETE_NOTIFICATION,
    BATCH_START_NOTIFICATION,
    CANCEL_REQUEST,
    DEPLOY_BATCH_COMPLETE_NOTIFICATION,
    DEPLOY_BATCH_START_NOTIFICATION,
    DEPLOY_COMPLETE_NOTIFICATION,
    DEPLOY_MESSAGE_NOTIFICATION,
    DISPOSE_REQUEST,
    EXECUTE_DEPLOY_REQUEST,
    EXECUTE_DOCUMENT_SELECTION_REQUEST,
    EXECUTE_DOCUMENT_STATEMENT_REQUEST,
    EXECUTE_STRING_REQUEST,
    MESSAGE_NOTIFICATION,
    QUERY_COMPLETE_NOTIFICATION,
    QUERY_EXECUTION_PLAN_REQUEST,
    RESULT_SET_COMPLETE_NOTIFICATION,
    SAVE_AS_CSV_REQUEST,
    SAVE_AS_EXCEL_REQUEST,
    SAVE_AS_JSON_REQUEST,
    SIMPLE_EXECUTE_REQUEST,
    SUBSET_REQUEST,
    BatchNotificationParams,
    ExecuteDocumentSelectionParams,
    ExecuteDocumentStatementParams,
    ExecuteRequestParamsBase,
    ExecuteStringParams,
    MessageNotificationParams,
    QueryCancelParams,
    QueryCancelResult,
    QueryCompleteNotificationParams,
    QueryDisposeParams,
    QueryExecutionPlanRequest,
    ResultMessage,
    ResultSetNotificationParams,
    SaveResultRequestResult,
    SaveResultsAsCsvRequestParams,
    SaveResultsAsExcelRequestParams,
    SaveResultsAsJsonRequestParams,
    SimpleExecuteRequest,
    SimpleExecuteResponse,
    SubsetParams,
)
from ossdbtoolsservice.utils import constants, time
from ossdbtoolsservice.utils.connection import get_db_error_message
from ossdbtoolsservice.workspace.workspace_service import WorkspaceService

NO_QUERY_MESSAGE = "QueryServiceRequestsNoQuery"

T = TypeVar("T")


class ExecuteRequestWorkerArgs:
    def __init__(
        self,
        owner_uri: str,
        connection: ServerConnection | PooledConnection,
        request_context: RequestContext,
        result_set_storage_type: ResultSetStorageType,
        before_query_initialize: Callable[[dict[str, Any]], None] | None = None,
        on_batch_start: Callable[[BatchNotificationParams], None] | None = None,
        on_message_notification: Callable[[MessageNotificationParams], None] | None = None,
        on_resultset_complete: Callable[[ResultSetNotificationParams], None] | None = None,
        on_batch_complete: Callable[[BatchNotificationParams], None] | None = None,
        on_query_complete: Callable[[QueryCompleteNotificationParams], None] | None = None,
    ) -> None:
        self.owner_uri = owner_uri
        self.connection = connection
        self.request_context = request_context
        self.result_set_storage_type = result_set_storage_type
        self.before_query_initialize = before_query_initialize
        self.on_batch_start = on_batch_start
        self.on_message_notification = on_message_notification
        self.on_resultset_complete = on_resultset_complete
        self.on_batch_complete = on_batch_complete
        self.on_query_complete = on_query_complete


class QueryExecutionService(Service):
    """Service for executing queries"""

    def __init__(self) -> None:
        self._service_provider: ServiceProvider | None = None
        # Dictionary mapping uri to a list of batches
        self.query_results: dict[str, Query] = {}
        self.owner_to_thread_map: dict = {}  # Only used for testing

        self._service_action_mapping: dict = {
            EXECUTE_STRING_REQUEST: self._handle_execute_query_request,
            EXECUTE_DEPLOY_REQUEST: self._handle_execute_deploy_request,  # Unused in VSCode
            EXECUTE_DOCUMENT_SELECTION_REQUEST: self._handle_execute_query_request,
            EXECUTE_DOCUMENT_STATEMENT_REQUEST: self._handle_execute_query_request,
            SUBSET_REQUEST: self._handle_subset_request,
            CANCEL_REQUEST: self._handle_cancel_query_request,
            SIMPLE_EXECUTE_REQUEST: self._handle_simple_execute_request,
            DISPOSE_REQUEST: self._handle_dispose_request,
            QUERY_EXECUTION_PLAN_REQUEST: self._handle_query_execution_plan_request,
            SAVE_AS_CSV_REQUEST: self._handle_save_as_csv_request,
            SAVE_AS_JSON_REQUEST: self._handle_save_as_json_request,
            SAVE_AS_EXCEL_REQUEST: self._handle_save_as_excel_request,
        }

    def register(self, service_provider: ServiceProvider) -> None:
        self._service_provider = service_provider
        # Register the request handlers with the server

        for action in self._service_action_mapping:
            self._service_provider.server.set_request_handler(
                action, self._service_action_mapping[action]
            )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info(
                "Query execution service successfully initialized"
            )

    def get_query(self, owner_uri: str | None) -> Query:
        if owner_uri is None:
            raise ValueError("owner_uri cannot be None")
        if owner_uri not in self.query_results:
            raise LookupError(f"No query found for owner_uri: {owner_uri}")
        return self.query_results[owner_uri]

    @property
    def service_provider(self) -> ServiceProvider:
        if self._service_provider is None:
            raise ValueError("Service provider is not set")
        return self._service_provider

    # REQUEST HANDLERS #####################################################

    def _handle_save_as_csv_request(
        self, request_context: RequestContext, params: SaveResultsAsCsvRequestParams
    ) -> None:
        self._save_result(params, request_context, SaveAsCsvFileStreamFactory(params))

    def _handle_save_as_json_request(
        self, request_context: RequestContext, params: SaveResultsAsJsonRequestParams
    ) -> None:
        self._save_result(params, request_context, SaveAsJsonFileStreamFactory(params))

    def _handle_save_as_excel_request(
        self, request_context: RequestContext, params: SaveResultsAsExcelRequestParams
    ) -> None:
        self._save_result(params, request_context, SaveAsExcelFileStreamFactory(params))

    def _handle_query_execution_plan_request(
        self, request_context: RequestContext, params: QueryExecutionPlanRequest
    ) -> Any:
        raise NotImplementedError()

    def _handle_simple_execute_request(
        self, request_context: RequestContext, params: SimpleExecuteRequest
    ) -> None:
        new_owner_uri = str(uuid.uuid4())

        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("Missing ownerUri")
            return

        connection_service = self.service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        )
        pooled_connection = connection_service.get_pooled_connection(owner_uri)
        if pooled_connection is None:
            request_context.send_error("Could not get connection info")
            return

        execute_params = ExecuteStringParams()
        execute_params.query = params.query_string
        execute_params.owner_uri = new_owner_uri

        def on_query_complete(query_complete_params: QueryCompleteNotificationParams) -> None:
            subset_params = SubsetParams()
            subset_params.owner_uri = new_owner_uri
            subset_params.batch_index = 0
            subset_params.result_set_index = 0
            subset_params.rows_start_index = 0

            if not query_complete_params.batch_summaries:
                request_context.send_error("Unable to get batch summaries")
                return

            resut_set_sumaries = query_complete_params.batch_summaries[0].result_set_summaries
            if not resut_set_sumaries:
                request_context.send_error("Unable to get result set summaries")
                return

            resultset_summary = resut_set_sumaries[0]

            subset_params.rows_count = resultset_summary.row_count

            subset = self._get_result_subset(request_context, subset_params)

            if subset is None:
                request_context.send_error("Unable to get result subset")
                return

            simple_execute_response = SimpleExecuteResponse(
                subset.result_subset.rows,
                subset.result_subset.row_count,
                resultset_summary.column_info,
            )
            request_context.send_response(simple_execute_response)

        worker_args = ExecuteRequestWorkerArgs(
            new_owner_uri,
            pooled_connection,
            request_context,
            ResultSetStorageType.FILE_STORAGE,
            on_query_complete=on_query_complete,
        )

        self._start_query_execution_thread(request_context, execute_params, worker_args)

    def _handle_execute_query_request(
        self, request_context: RequestContext, params: ExecuteRequestParamsBase
    ) -> None:
        """Kick off thread to execute query
        in response to an incoming execute query request"""

        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("Missing ownerUri")
            return

        def before_query_initialize(before_query_initialize_params: dict[str, Any]) -> None:
            # Send a response to indicate that the query was kicked off
            request_context.send_response(before_query_initialize_params)

        def on_batch_start(batch_event_params: BatchNotificationParams) -> None:
            request_context.send_notification(BATCH_START_NOTIFICATION, batch_event_params)

        def on_message_notification(notice_message_params: MessageNotificationParams) -> None:
            request_context.send_notification(MESSAGE_NOTIFICATION, notice_message_params)

        def on_resultset_complete(result_set_params: ResultSetNotificationParams) -> None:
            # query/resultSetAvailable not used in VSCode.
            # request_context.send_notification(
            #     RESULT_SET_AVAILABLE_NOTIFICATION, result_set_params
            # )
            request_context.send_notification(
                RESULT_SET_COMPLETE_NOTIFICATION, result_set_params
            )

        def on_batch_complete(batch_event_params: BatchNotificationParams) -> None:
            request_context.send_notification(BATCH_COMPLETE_NOTIFICATION, batch_event_params)

        def on_query_complete(query_complete_params: QueryCompleteNotificationParams) -> None:
            request_context.send_notification(
                QUERY_COMPLETE_NOTIFICATION, query_complete_params
            )

        # Get a connection for the query
        try:
            connection = self._get_long_lived_connection(owner_uri)
        except Exception as e:
            if self.service_provider.logger is not None:
                self.service_provider.logger.exception(
                    "Encountered exception while handling query request"
                )  # TODO: Localize
            request_context.send_error(str(e))
            return

        worker_args = ExecuteRequestWorkerArgs(
            owner_uri,
            connection,
            request_context,
            ResultSetStorageType.FILE_STORAGE,
            before_query_initialize,
            on_batch_start,
            on_message_notification,
            on_resultset_complete,
            on_batch_complete,
            on_query_complete,
        )

        self._start_query_execution_thread(request_context, params, worker_args)

    def _handle_execute_deploy_request(
        self, request_context: RequestContext, params: ExecuteRequestParamsBase
    ) -> None:
        """Kick off thread to execute query
        in response to an incoming execute query request"""

        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("Missing ownerUri")
            return

        def before_query_initialize(before_query_initialize_params: dict[str, Any]) -> None:
            # Send a response to indicate that the query was kicked off
            request_context.send_response(before_query_initialize_params)

        def on_batch_start(batch_event_params: BatchNotificationParams) -> None:
            request_context.send_notification(
                DEPLOY_BATCH_START_NOTIFICATION, batch_event_params
            )

        def on_message_notification(notice_message_params: MessageNotificationParams) -> None:
            request_context.send_notification(
                DEPLOY_MESSAGE_NOTIFICATION, notice_message_params
            )

        def on_resultset_complete(result_set_params: ResultSetNotificationParams) -> None:
            pass

        def on_batch_complete(batch_event_params: BatchNotificationParams) -> None:
            request_context.send_notification(
                DEPLOY_BATCH_COMPLETE_NOTIFICATION, batch_event_params
            )

        def on_query_complete(query_complete_params: QueryCompleteNotificationParams) -> None:
            request_context.send_notification(
                DEPLOY_COMPLETE_NOTIFICATION, query_complete_params
            )

        # Get a connection for the query
        try:
            connection = self._get_long_lived_connection(owner_uri)
        except Exception as e:
            if self.service_provider.logger is not None:
                self.service_provider.logger.exception(
                    "Encountered exception while handling query request"
                )  # TODO: Localize
            request_context.send_error(str(e))
            return

        worker_args = ExecuteRequestWorkerArgs(
            owner_uri,
            connection,
            request_context,
            ResultSetStorageType.FILE_STORAGE,
            before_query_initialize,
            on_batch_start,
            on_message_notification,
            on_resultset_complete,
            on_batch_complete,
            on_query_complete,
        )

        self._start_query_execution_thread(request_context, params, worker_args)

    def _start_query_execution_thread(
        self,
        request_context: RequestContext,
        params: ExecuteRequestParamsBase,
        worker_args: ExecuteRequestWorkerArgs,
    ) -> None:
        if params.owner_uri is None:
            request_context.send_error("Missing ownerUri")
            return

        # Set up batch execution callback methods for sending notifications
        def _batch_execution_started_callback(batch: Batch) -> None:
            batch_event_params = BatchNotificationParams(
                batch.batch_summary, worker_args.owner_uri
            )
            _check_and_fire(worker_args.on_batch_start, batch_event_params)

        def _batch_execution_finished_callback(batch: Batch) -> None:
            # Send back notices as a separate message to
            # avoid error coloring / highlighting of text
            notices = batch.notices
            if notices:
                notice_messages = "\n".join(notices)
                notice_message_params = self.build_message_params(
                    worker_args.owner_uri, batch.id, notice_messages, False
                )
                _check_and_fire(worker_args.on_message_notification, notice_message_params)

            batch_summary = batch.batch_summary

            # send query/resultSetComplete response
            result_set_params = self.build_result_set_complete_params(
                batch_summary, worker_args.owner_uri
            )
            _check_and_fire(worker_args.on_resultset_complete, result_set_params)

            # If the batch was successful, send a message to the client
            if not batch.has_error:
                rows_message = _create_rows_affected_message(batch)
                message_params = self.build_message_params(
                    worker_args.owner_uri, batch.id, rows_message, False
                )
                _check_and_fire(worker_args.on_message_notification, message_params)

            # send query/batchComplete and query/complete response
            batch_event_params = BatchNotificationParams(batch_summary, worker_args.owner_uri)
            _check_and_fire(worker_args.on_batch_complete, batch_event_params)

        # Create a new query if one does not already exist
        # or we already executed the previous one
        if (
            params.owner_uri not in self.query_results
            or self.query_results[params.owner_uri].execution_state is ExecutionState.EXECUTED
        ):
            query_text = self._get_query_text_from_execute_params(params)

            if query_text is None:
                request_context.send_error("Unable to determine query text.")
                return

            execution_settings = QueryExecutionSettings(
                params.execution_plan_options, worker_args.result_set_storage_type
            )
            query_events = QueryEvents(
                None,
                None,
                BatchEvents(
                    _batch_execution_started_callback, _batch_execution_finished_callback
                ),
            )
            self.query_results[params.owner_uri] = Query(
                params.owner_uri, query_text, execution_settings, query_events
            )
        elif self.query_results[params.owner_uri].execution_state is ExecutionState.EXECUTING:
            request_context.send_error(
                "Another query is currently executing."
            )  # TODO: Localize
            return

        thread = threading.Thread(
            target=self._execute_query_request_worker, args=(worker_args,)
        )
        self.owner_to_thread_map[params.owner_uri] = thread
        thread.daemon = True
        thread.start()

    def _handle_subset_request(
        self, request_context: RequestContext, params: SubsetParams
    ) -> None:
        """Sends a response back to the query/subset request"""
        result = self._get_result_subset(request_context, params)
        if result is not None:
            request_context.send_response(result)

    def _get_result_subset(
        self, request_context: RequestContext, params: SubsetParams
    ) -> SubsetResult | None:
        try:
            query: Query = self.get_query(params.owner_uri)

            if query is None:
                request_context.send_error(NO_QUERY_MESSAGE)
                return None

            if params.batch_index is None:
                request_context.send_error("Missing batch index")
                return None
            if params.result_set_index is None:
                request_context.send_error("Missing result set index")
                return None
            if params.rows_start_index is None:
                request_context.send_error("Missing rows start index")
                return None
            if params.rows_count is None:
                request_context.send_error("Missing rows count")
                return None

            result_set_subset = query.get_subset(
                params.batch_index,
                params.rows_start_index,
                params.rows_start_index + params.rows_count,
            )

            return SubsetResult(result_set_subset)
        except Exception as e:
            request_context.send_unhandled_error_response(e)
            return None

    def _handle_cancel_query_request(
        self, request_context: RequestContext, params: QueryCancelParams
    ) -> None:
        """Handles a 'query/cancel' request"""
        try:
            if params.owner_uri in self.query_results:
                query = self.query_results[params.owner_uri]
            else:
                request_context.send_response(
                    QueryCancelResult(NO_QUERY_MESSAGE)
                )  # TODO: Localize
                return

            # Only cancel the query if we're in a cancellable state
            if query.execution_state is ExecutionState.EXECUTED:
                request_context.send_response(
                    QueryCancelResult("Query already executed")
                )  # TODO: Localize
                return

            query.is_canceled = True

            # Only need to do additional work to cancel the query
            # if it's currently running
            if query.execution_state is ExecutionState.EXECUTING:
                self.cancel_query(params.owner_uri, query)
            request_context.send_response(QueryCancelResult())

        except Exception as e:
            self._log_exception(e)
            request_context.send_unhandled_error_response(e)

    def _handle_dispose_request(
        self, request_context: RequestContext, params: QueryDisposeParams
    ) -> None:
        try:
            owner_uri = params.owner_uri
            if owner_uri is None:
                request_context.send_error(NO_QUERY_MESSAGE)  # TODO: Localize
                return

            query = self.query_results.get(owner_uri)
            if not query:
                request_context.send_error(NO_QUERY_MESSAGE)  # TODO: Localize
                return
            # Make sure to cancel the query first if it's not executed.
            # If it's not started, then make sure it never starts.
            # If it's executing, make sure that we stop it
            if query.execution_state is not ExecutionState.EXECUTED:
                self.cancel_query(owner_uri, query)
            del self.query_results[owner_uri]
            request_context.send_response({})
        except Exception as e:
            request_context.send_unhandled_error_response(e)

    def cancel_query(self, owner_uri: str, query: Query) -> None:
        pooled_connection = self._get_pooled_connection(owner_uri)
        if pooled_connection is None:
            raise LookupError("Could not find associated connection")  # TODO: Localize

        if query.connection_backend_pid is None:
            return  # Query is no longer running

        with pooled_connection as conn:
            conn.execute_query(f"SELECT pg_cancel_backend ({query.connection_backend_pid})")

    def _execute_query_request_worker(
        self, worker_args: ExecuteRequestWorkerArgs, retry_state: bool = False
    ) -> None:
        """Worker method for 'handle execute query request' thread"""

        _check_and_fire(worker_args.before_query_initialize, {})

        query: Query = self.query_results[worker_args.owner_uri]

        # Wrap execution in a try/except block so that we can send an error if it fails
        try:
            if isinstance(worker_args.connection, ServerConnection):
                query.execute(worker_args.connection, retry_state)
            else:
                # PooledConnection, use as context manager.
                with worker_args.connection as connection:
                    query.execute(connection, retry_state)
        except Exception as e:
            self._resolve_query_exception(e, query, worker_args)
        finally:
            # Send a query complete notification
            batch_summaries = [batch.batch_summary for batch in query.batches]

            query_complete_params = QueryCompleteNotificationParams(
                worker_args.owner_uri, batch_summaries
            )
            _check_and_fire(worker_args.on_query_complete, query_complete_params)

    def _get_pooled_connection(self, owner_uri: str) -> PooledConnection:
        """
        Get a pooled connection for the given owner URI from the connection service

        :param owner_uri: the URI to get the connection for
        :returns: a PooledConnection object
        :raises LookupError: if there is no connection service
        :raises ValueError: if there is no pooled connection
            corresponding to the given owner_uri
        """
        connection_service = self.service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        )
        connection = connection_service.get_pooled_connection(owner_uri)
        if connection is None:
            raise ValueError(f"No connection for owner URI: {owner_uri}")
        return connection

    def _get_long_lived_connection(self, owner_uri: str) -> ServerConnection:
        """
        Get a long lived connection for the given owner URI from the connection service

        :param owner_uri: the URI to get the connection for
        :returns: a ServerConnection object
        :raises LookupError: if there is no connection service
        :raises ValueError: if there is no connection pool
            corresponding to the given owner_uri
        """
        connection_service = self.service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        )
        connection = connection_service.get_connection(owner_uri, owner_uri[-30:])
        if connection is None:
            raise ValueError(f"No connection for owner URI: {owner_uri}")
        return connection

    def build_result_set_complete_params(
        self, summary: BatchSummary, owner_uri: str
    ) -> ResultSetNotificationParams:
        summaries = summary.result_set_summaries
        result_set_summary = None
        # Check if none or empty list
        if summaries:
            result_set_summary = summaries[0]
        return ResultSetNotificationParams(
            owner_uri=owner_uri, result_set_summary=result_set_summary
        )

    def build_message_params(
        self, owner_uri: str, batch_id: int, message: str, is_error: bool = False
    ) -> MessageNotificationParams:
        result_message = ResultMessage(
            batch_id=batch_id,
            is_error=is_error,
            time=time.get_time_str(datetime.now()),
            message=message,
        )
        return MessageNotificationParams(owner_uri=owner_uri, message=result_message)

    def _get_query_text_from_execute_params(
        self, params: ExecuteRequestParamsBase
    ) -> str | None:
        if isinstance(params, ExecuteDocumentSelectionParams):
            if params.owner_uri is None:
                return None

            workspace_service = self.service_provider.get(
                constants.WORKSPACE_SERVICE_NAME, WorkspaceService
            )
            selection_range = (
                params.query_selection.to_range()
                if params.query_selection is not None
                else None
            )

            return workspace_service.get_text(params.owner_uri, selection_range)

        elif isinstance(params, ExecuteDocumentStatementParams):
            # TODO: Move this model to pydantic so validation can
            # occur automatically and be specific about issues with messages.
            owner_uri = params.owner_uri
            if owner_uri is None:
                return None
            line = params.line
            column = params.column
            if line is None or column is None:
                return None

            workspace_service = self.service_provider.get(
                constants.WORKSPACE_SERVICE_NAME, WorkspaceService
            )
            query = workspace_service.get_text(owner_uri, None)
            selection_data_list: list[SelectionData] = compute_batches(
                sqlparse.split(query), query
            )

            for selection_data in selection_data_list:
                start_line = selection_data.start_line
                end_line = selection_data.end_line
                if start_line is None or end_line is None:
                    continue

                start_column = selection_data.start_column
                end_column = selection_data.end_column
                if start_column is None or end_column is None:
                    continue

                if start_line <= line and end_line >= line:
                    if (
                        selection_data.end_line == params.line
                        and end_column < column
                        or selection_data.start_line == params.line
                        and start_column > column
                    ):
                        continue
                    return workspace_service.get_text(owner_uri, selection_data.to_range())

            return None

        elif isinstance(params, ExecuteStringParams):
            return params.query
        else:
            return None

    def _resolve_query_exception(
        self,
        e: Exception,
        query: Query,
        worker_args: ExecuteRequestWorkerArgs,
        is_rollback_error: bool = False,
        retry_query: bool = False,
    ) -> None:
        self._log_debug(
            f"Query execution failed for following query: {query.query_text}\n {e}",
        )

        if retry_query:
            error_message = (
                "Server closed the connection unexpectedly. Attempting to reconnect..."
            )

        # If the error relates to the database, display the appropriate error
        # message based on the provider
        elif isinstance(
            e,
            (
                psycopg.DatabaseError,
                psycopg.errors.QueryCanceled,
            ),
        ):
            # get_error_message may return None so ensure error_message is str type
            error_message = str(get_db_error_message(e))

        elif isinstance(e, RuntimeError):
            error_message = str(e)

        else:
            error_message = (
                f"Unhandled exception while executing query: {str(e)}"  # TODO: Localize
            )
            if self.service_provider.logger is not None:
                self.service_provider.logger.exception(
                    "Unhandled exception while executing query"
                )

        # If the error occured during rollback, add a note about it
        if is_rollback_error:
            error_message = (
                "Error while rolling back open transaction due to previous failure: "
                + error_message
            )  # TODO: Localize

        # Send a message with the error to the client
        is_error_notification = not retry_query
        result_message_params = self.build_message_params(
            query.owner_uri,
            query.batches[query.current_batch_index].id,
            error_message,
            is_error_notification,
        )
        _check_and_fire(worker_args.on_message_notification, result_message_params)

        # Don't roll back transaction.
        # If the user opened the transaction, they should roll it back.
        # If the user did not open the transaction, the connection is in autocommit mode
        # and the transaction will be rolled back automatically.

    def _save_result(
        self,
        params: SaveResultsRequestParams,
        request_context: RequestContext,
        file_factory: FileStreamFactory,
    ) -> None:
        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("Missing ownerUri")
            return

        query: Query = self.query_results[owner_uri]

        def on_success() -> None:
            request_context.send_response(SaveResultRequestResult())

        def on_error(exc: Exception) -> None:
            file_path = params.file_path
            if file_path is None:
                file_path = "unknown"
            message = f"Failed to save {ntpath.basename(file_path)}: {exc}"
            request_context.send_error(message)

        try:
            query.save_as(params, file_factory, on_success, on_error)

        except Exception as error:
            on_error(error)


def _create_rows_affected_message(batch: Batch) -> str:
    # Only add in rows affected if the batch's row count is not -1.
    # Row count is automatically -1 when an operation occurred that
    # a row count cannot be determined for or execute() was not performed
    if batch.row_count != -1:
        return f"({batch.row_count} row(s) affected)"  # TODO: Localize
    elif batch.status_message is not None:
        return batch.status_message
    else:
        return "Commands completed successfully"  # TODO: Localize


def _check_and_fire(action: Callable[[T], None] | None, params: T) -> None:
    if action is not None:
        action(params)
