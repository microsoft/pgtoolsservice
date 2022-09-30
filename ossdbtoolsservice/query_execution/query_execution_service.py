# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
import threading
import uuid
from typing import Callable, Dict, List, Optional  # noqa
import sqlparse
import ntpath


from ossdbtoolsservice.hosting import RequestContext, ServiceProvider
from ossdbtoolsservice.query import (
    Batch, BatchEvents, ExecutionState, QueryExecutionSettings, Query, QueryEvents,
    compute_selection_data_for_batches as compute_batches
)
from ossdbtoolsservice.query.contracts import BatchSummary, ResultSetSubset, SelectionData, SaveResultsRequestParams, SubsetResult  # noqa
from ossdbtoolsservice.query import ResultSetStorageType
from ossdbtoolsservice.query_execution.contracts import (
    EXECUTE_STRING_REQUEST, EXECUTE_DEPLOY_REQUEST, EXECUTE_DOCUMENT_SELECTION_REQUEST, ExecuteRequestParamsBase,
    BATCH_START_NOTIFICATION, BATCH_COMPLETE_NOTIFICATION,
    DEPLOY_BATCH_COMPLETE_NOTIFICATION, DEPLOY_BATCH_START_NOTIFICATION, EXECUTE_DOCUMENT_STATEMENT_REQUEST,
    ExecuteDocumentStatementParams, ExecutionPlanOptions, ResultSetNotificationParams,
    MESSAGE_NOTIFICATION, DEPLOY_MESSAGE_NOTIFICATION, RESULT_SET_AVAILABLE_NOTIFICATION, RESULT_SET_COMPLETE_NOTIFICATION, MessageNotificationParams,
    QUERY_COMPLETE_NOTIFICATION, DEPLOY_COMPLETE_NOTIFICATION, QUERY_EXECUTION_PLAN_REQUEST, QueryCancelResult, QueryExecutionPlanRequest,
    SUBSET_REQUEST, ExecuteDocumentSelectionParams, CANCEL_REQUEST, QueryCancelParams, ResultMessage, SubsetParams,
    BatchNotificationParams, QueryCompleteNotificationParams, QueryDisposeParams,
    DISPOSE_REQUEST, SIMPLE_EXECUTE_REQUEST, SimpleExecuteRequest, ExecuteStringParams,
    SimpleExecuteResponse, SAVE_AS_CSV_REQUEST, SAVE_AS_JSON_REQUEST, SAVE_AS_EXCEL_REQUEST, SAVE_AS_XML_REQUEST, 
    SaveResultsAsJsonRequestParams, SaveResultRequestResult,
    SaveResultsAsCsvRequestParams, SaveResultsAsExcelRequestParams, SaveResultsAsXmlRequestParams
)

from ossdbtoolsservice.driver import ServerConnection
from ossdbtoolsservice.connection.contracts import ConnectRequestParams
from ossdbtoolsservice.connection.contracts import ConnectionType
import ossdbtoolsservice.utils as utils
from ossdbtoolsservice.query.data_storage import (
    FileStreamFactory, SaveAsCsvFileStreamFactory, SaveAsJsonFileStreamFactory, SaveAsExcelFileStreamFactory, SaveAsXmlFileStreamFactory
)


NO_QUERY_MESSAGE = 'QueryServiceRequestsNoQuery'


class ExecuteRequestWorkerArgs():

    def __init__(self, owner_uri: str, connection: ServerConnection, request_context: RequestContext, result_set_storage_type,
                 before_query_initialize: Callable = None, on_batch_start: Callable = None, on_message_notification: Callable = None,
                 on_resultset_complete: Callable = None, on_batch_complete: Callable = None, on_query_complete: Callable = None):

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


class QueryExecutionService(object):
    """Service for executing queries"""

    def __init__(self):
        self._service_provider: ServiceProvider = None
        # Dictionary mapping uri to a list of batches
        self.query_results: Dict[str, Query] = {}
        self.owner_to_thread_map: dict = {}  # Only used for testing

        self._service_action_mapping: dict = {
            EXECUTE_STRING_REQUEST: self._handle_execute_query_request,
            EXECUTE_DEPLOY_REQUEST: self._handle_execute_deploy_request,
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
            SAVE_AS_XML_REQUEST: self._handle_save_as_xml_request
        }

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider
        # Register the request handlers with the server

        for action in self._service_action_mapping:
            self._service_provider.server.set_request_handler(action, self._service_action_mapping[action])

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Query execution service successfully initialized')

    def get_query(self, owner_uri: str):
        return self.query_results[owner_uri]

    # REQUEST HANDLERS #####################################################

    def _handle_save_as_csv_request(self, request_context: RequestContext, params: SaveResultsAsCsvRequestParams) -> None:
        self._save_result(params, request_context, SaveAsCsvFileStreamFactory(params))

    def _handle_save_as_json_request(self, request_context: RequestContext, params: SaveResultsAsJsonRequestParams) -> None:
        self._save_result(params, request_context, SaveAsJsonFileStreamFactory(params))

    def _handle_save_as_excel_request(self, request_context: RequestContext, params: SaveResultsAsExcelRequestParams) -> None:
        self._save_result(params, request_context, SaveAsExcelFileStreamFactory(params))

    def _handle_save_as_xml_request(self, request_context: RequestContext, params: SaveResultsAsXmlRequestParams) -> None:
        self._save_result(params, request_context, SaveAsXmlFileStreamFactory(params))

    def _handle_query_execution_plan_request(self, request_context: RequestContext, params: QueryExecutionPlanRequest):
        raise NotImplementedError()

    def _handle_simple_execute_request(self, request_context: RequestContext, params: SimpleExecuteRequest):

        new_owner_uri = str(uuid.uuid4())

        connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
        connection_info = connection_service.get_connection_info(params.owner_uri)
        connection_service.connect(ConnectRequestParams(connection_info.details, new_owner_uri, ConnectionType.QUERY))
        new_connection = self._get_connection(new_owner_uri, ConnectionType.QUERY)

        execute_params = ExecuteStringParams()
        execute_params.query = params.query_string
        execute_params.owner_uri = new_owner_uri

        def on_query_complete(query_complete_params):
            subset_params = SubsetParams()
            subset_params.owner_uri = new_owner_uri
            subset_params.batch_index = 0
            subset_params.result_set_index = 0
            subset_params.rows_start_index = 0

            resultset_summary = query_complete_params.batch_summaries[0].result_set_summaries[0]

            subset_params.rows_count = resultset_summary.row_count

            subset = self._get_result_subset(request_context, subset_params)

            simple_execute_response = SimpleExecuteResponse(subset.result_subset.rows, subset.result_subset.row_count, resultset_summary.column_info)
            request_context.send_response(simple_execute_response)

        worker_args = ExecuteRequestWorkerArgs(new_owner_uri, new_connection, request_context, ResultSetStorageType.FILE_STORAGE,
                                               on_query_complete=on_query_complete)

        self._start_query_execution_thread(request_context, execute_params, worker_args)

    def _handle_execute_query_request(
        self, request_context: RequestContext, params: ExecuteRequestParamsBase
    ) -> None:
        """Kick off thread to execute query in response to an incoming execute query request"""

        def before_query_initialize(before_query_initialize_params):
            # Send a response to indicate that the query was kicked off
            request_context.send_response(before_query_initialize_params)

        def on_batch_start(batch_event_params):
            request_context.send_notification(BATCH_START_NOTIFICATION, batch_event_params)

        def on_message_notification(notice_message_params):
            request_context.send_notification(MESSAGE_NOTIFICATION, notice_message_params)

        def on_resultset_complete(result_set_params):
            request_context.send_notification(RESULT_SET_AVAILABLE_NOTIFICATION, result_set_params)
            request_context.send_notification(RESULT_SET_COMPLETE_NOTIFICATION, result_set_params)

        def on_batch_complete(batch_event_params):
            request_context.send_notification(BATCH_COMPLETE_NOTIFICATION, batch_event_params)

        def on_query_complete(query_complete_params):
            request_context.send_notification(QUERY_COMPLETE_NOTIFICATION, query_complete_params)

        # Get a connection for the query
        try:
            conn = self._get_connection(params.owner_uri, ConnectionType.QUERY)
        except Exception as e:
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception(
                    'Encountered exception while handling query request')  # TODO: Localize
            request_context.send_unhandled_error_response(e)
            return

        worker_args = ExecuteRequestWorkerArgs(params.owner_uri, conn, request_context, ResultSetStorageType.FILE_STORAGE, before_query_initialize,
                                               on_batch_start, on_message_notification, on_resultset_complete,
                                               on_batch_complete, on_query_complete)

        self._start_query_execution_thread(request_context, params, worker_args)

    def _handle_execute_deploy_request(
        self, request_context: RequestContext, params: ExecuteRequestParamsBase
    ) -> None:
        """Kick off thread to execute query in response to an incoming execute query request"""

        def before_query_initialize(before_query_initialize_params):
            # Send a response to indicate that the query was kicked off
            request_context.send_response(before_query_initialize_params)

        def on_batch_start(batch_event_params):
            request_context.send_notification(DEPLOY_BATCH_START_NOTIFICATION, batch_event_params)

        def on_message_notification(notice_message_params):
            request_context.send_notification(DEPLOY_MESSAGE_NOTIFICATION, notice_message_params)

        def on_resultset_complete(result_set_params):
            pass

        def on_batch_complete(batch_event_params):
            request_context.send_notification(DEPLOY_BATCH_COMPLETE_NOTIFICATION, batch_event_params)

        def on_query_complete(query_complete_params):
            request_context.send_notification(DEPLOY_COMPLETE_NOTIFICATION, query_complete_params)

        # Get a connection for the query
        try:
            conn = self._get_connection(params.owner_uri, ConnectionType.QUERY)
        except Exception as e:
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception(
                    'Encountered exception while handling query request')  # TODO: Localize
            request_context.send_unhandled_error_response(e)
            return

        worker_args = ExecuteRequestWorkerArgs(params.owner_uri, conn, request_context, ResultSetStorageType.FILE_STORAGE, before_query_initialize,
                                               on_batch_start, on_message_notification, on_resultset_complete,
                                               on_batch_complete, on_query_complete)

        self._start_query_execution_thread(request_context, params, worker_args)

    def _start_query_execution_thread(self, request_context: RequestContext, params: ExecuteRequestParamsBase, worker_args: ExecuteRequestWorkerArgs = None):

        # Set up batch execution callback methods for sending notifications
        def _batch_execution_started_callback(batch: Batch) -> None:
            batch_event_params = BatchNotificationParams(batch.batch_summary, worker_args.owner_uri)
            _check_and_fire(worker_args.on_batch_start, batch_event_params)

        def _batch_execution_finished_callback(batch: Batch) -> None:
            # Send back notices as a separate message to avoid error coloring / highlighting of text
            notices = batch.notices
            if notices:
                notice_message_params = self.build_message_params(worker_args.owner_uri, batch.id, ''.join(notices), False)
                _check_and_fire(worker_args.on_message_notification, notice_message_params)

            batch_summary = batch.batch_summary

            # send query/resultSetComplete response
            result_set_params = self.build_result_set_complete_params(batch_summary, worker_args.owner_uri)
            _check_and_fire(worker_args.on_resultset_complete, result_set_params)

            # If the batch was successful, send a message to the client
            if not batch.has_error:
                rows_message = _create_rows_affected_message(batch)
                message_params = self.build_message_params(worker_args.owner_uri, batch.id, rows_message, False)
                _check_and_fire(worker_args.on_message_notification, message_params)

            # send query/batchComplete and query/complete response
            batch_event_params = BatchNotificationParams(batch_summary, worker_args.owner_uri)
            _check_and_fire(worker_args.on_batch_complete, batch_event_params)

        # Create a new query if one does not already exist or we already executed the previous one
        if params.owner_uri not in self.query_results or self.query_results[params.owner_uri].execution_state is ExecutionState.EXECUTED:
            query_text = self._get_query_text_from_execute_params(params)

            execution_settings = QueryExecutionSettings(params.execution_plan_options, worker_args.result_set_storage_type)
            query_events = QueryEvents(None, None, BatchEvents(_batch_execution_started_callback, _batch_execution_finished_callback))
            self.query_results[params.owner_uri] = Query(params.owner_uri, query_text, execution_settings, query_events)
        elif self.query_results[params.owner_uri].execution_state is ExecutionState.EXECUTING:
            request_context.send_error('Another query is currently executing.')  # TODO: Localize
            return

        thread = threading.Thread(
            target=self._execute_query_request_worker,
            args=(worker_args,)
        )
        self.owner_to_thread_map[params.owner_uri] = thread
        thread.daemon = True
        thread.start()

    def _handle_subset_request(self, request_context: RequestContext, params: SubsetParams):
        """Sends a response back to the query/subset request"""
        request_context.send_response(self._get_result_subset(request_context, params))

    def _get_result_subset(self, request_context: RequestContext, params: SubsetParams) -> SubsetResult:
        query: Query = self.get_query(params.owner_uri)

        result_set_subset = query.get_subset(
            params.batch_index,
            params.rows_start_index,
            params.rows_start_index + params.rows_count)

        return SubsetResult(result_set_subset)

    def _handle_cancel_query_request(self, request_context: RequestContext, params: QueryCancelParams):
        """Handles a 'query/cancel' request"""
        try:
            if params.owner_uri in self.query_results:
                query = self.query_results[params.owner_uri]
            else:
                request_context.send_response(QueryCancelResult(NO_QUERY_MESSAGE))  # TODO: Localize
                return

            # Only cancel the query if we're in a cancellable state
            if query.execution_state is ExecutionState.EXECUTED:
                request_context.send_response(QueryCancelResult('Query already executed'))  # TODO: Localize
                return

            query.is_canceled = True

            # Only need to do additional work to cancel the query
            # if it's currently running
            if query.execution_state is ExecutionState.EXECUTING:
                self.cancel_query(params.owner_uri)
            request_context.send_response(QueryCancelResult())

        except Exception as e:
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception(str(e))
            request_context.send_unhandled_error_response(e)

    def _handle_dispose_request(self, request_context: RequestContext, params: QueryDisposeParams):
        try:
            if params.owner_uri not in self.query_results:
                request_context.send_error(NO_QUERY_MESSAGE)  # TODO: Localize
                return
            # Make sure to cancel the query first if it's not executed.
            # If it's not started, then make sure it never starts. If it's executing, make sure
            # that we stop it
            if self.query_results[params.owner_uri].execution_state is not ExecutionState.EXECUTED:
                self.cancel_query(params.owner_uri)
            del self.query_results[params.owner_uri]
            request_context.send_response({})
        except Exception as e:
            request_context.send_unhandled_error_response(e)

    def cancel_query(self, owner_uri: str):
        conn = self._get_connection(owner_uri, ConnectionType.QUERY)
        cancel_conn = self._get_connection(owner_uri, ConnectionType.QUERY_CANCEL)
        if conn is None or cancel_conn is None:
            raise LookupError('Could not find associated connection')  # TODO: Localize

        try:
            cancel_conn.execute_query(conn.cancellation_query)
        # This exception occurs when we run SELECT pg_cancel_backend on
        # a query that's currently executing
        except BaseException:
            raise

    def _execute_query_request_worker(self, worker_args: ExecuteRequestWorkerArgs):
        """Worker method for 'handle execute query request' thread"""

        _check_and_fire(worker_args.before_query_initialize, {})

        query: Query = self.query_results[worker_args.owner_uri]

        # Wrap execution in a try/except block so that we can send an error if it fails
        try:
            query.execute(worker_args.connection)
        except Exception as e:
            self._resolve_query_exception(e, query, worker_args)
        finally:
            # Send a query complete notification
            batch_summaries = [batch.batch_summary for batch in query.batches]

            query_complete_params = QueryCompleteNotificationParams(worker_args.owner_uri, batch_summaries)
            _check_and_fire(worker_args.on_query_complete, query_complete_params)

    def _get_connection(self, owner_uri: str, connection_type: ConnectionType) -> ServerConnection:
        """
        Get a connection for the given owner URI and connection type from the connection service

        :param owner_uri: the URI to get the connection for
        :param connection_type: the type of connection to get
        :returns: a ServerConnection object
        :raises LookupError: if there is no connection service
        :raises ValueError: if there is no connection corresponding to the given owner_uri
        """
        connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
        return connection_service.get_connection(owner_uri, connection_type)

    def build_result_set_complete_params(self, summary: BatchSummary, owner_uri: str) -> ResultSetNotificationParams:
        summaries = summary.result_set_summaries
        result_set_summary = None
        # Check if none or empty list
        if summaries:
            result_set_summary = summaries[0]
        return ResultSetNotificationParams(owner_uri, result_set_summary)

    def build_message_params(self, owner_uri: str, batch_id: int, message: str, is_error: bool = False):
        result_message = ResultMessage(batch_id, is_error, utils.time.get_time_str(datetime.now()), message)
        return MessageNotificationParams(owner_uri, result_message)

    def _get_query_text_from_execute_params(self, params: ExecuteRequestParamsBase):
        if isinstance(params, ExecuteDocumentSelectionParams):
            workspace_service = self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME]
            selection_range = params.query_selection.to_range() if params.query_selection is not None else None

            return workspace_service.get_text(params.owner_uri, selection_range)

        elif isinstance(params, ExecuteDocumentStatementParams):
            workspace_service = self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME]
            query = workspace_service.get_text(params.owner_uri, None)
            selection_data_list: List[SelectionData] = compute_batches(sqlparse.split(query), query)

            for selection_data in selection_data_list:
                if selection_data.start_line <= params.line and selection_data.end_line >= params.line:
                    if (selection_data.end_line == params.line and selection_data.end_column < params.column or
                            selection_data.start_line == params.line and selection_data.start_column > params.column):
                        continue
                    return workspace_service.get_text(params.owner_uri, selection_data.to_range())

            return ''

        else:
            # Then params must be an instance of ExecuteStringParams, which has the query as an attribute
            return params.query

    def _resolve_query_exception(self, e: Exception, query: Query, worker_args: ExecuteRequestWorkerArgs, is_rollback_error=False):
        utils.log.log_debug(self._service_provider.logger, f'Query execution failed for following query: {query.query_text}\n {e}')

        # If the error relates to the database, display the appropriate error message based on the provider
        if isinstance(e, worker_args.connection.database_error) or isinstance(e, worker_args.connection.query_canceled_error):
            # get_error_message may return None so ensure error_message is str type
            error_message = str(worker_args.connection.get_error_message(e))

        elif isinstance(e, RuntimeError):
            error_message = str(e)

        else:
            error_message = 'Unhandled exception while executing query: {}'.format(str(e))  # TODO: Localize
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception('Unhandled exception while executing query')

        # If the error occured during rollback, add a note about it
        if is_rollback_error:
            error_message = 'Error while rolling back open transaction due to previous failure: ' + error_message  # TODO: Localize

        # Send a message with the error to the client
        result_message_params = self.build_message_params(query.owner_uri, query.batches[query.current_batch_index].id, error_message, True)
        _check_and_fire(worker_args.on_message_notification, result_message_params)

        # If there was a failure in the middle of a transaction, roll it back.
        # Note that conn.rollback() won't work since the connection is in autocommit mode
        if not is_rollback_error and worker_args.connection.transaction_in_error:
            rollback_query = Query(query.owner_uri, 'ROLLBACK', QueryExecutionSettings(ExecutionPlanOptions(), None), QueryEvents())
            try:
                rollback_query.execute(worker_args.connection)
            except Exception as rollback_exception:
                # If the rollback failed, handle the error as usual but don't try to roll back again
                self._resolve_query_exception(rollback_exception, rollback_query, worker_args, True)

    def _save_result(self, params: SaveResultsRequestParams, request_context: RequestContext, file_factory: FileStreamFactory):
        query: Query = self.query_results[params.owner_uri]

        def on_success():
            request_context.send_response(SaveResultRequestResult())

        def on_error(reason: str):
            message = 'Failed to save {0}: {1}'.format(ntpath.basename(params.file_path), reason)
            request_context.send_error(message)

        try:
            query.save_as(params, file_factory, on_success, on_error)

        except Exception as error:
            on_error(str(error))


def _create_rows_affected_message(batch: Batch) -> str:
    # Only add in rows affected if the batch's row count is not -1.
    # Row count is automatically -1 when an operation occurred that
    # a row count cannot be determined for or execute() was not performed
    if batch.row_count != -1:
        return '({0} row(s) affected)'.format(batch.row_count)  # TODO: Localize
    else:
        return 'Commands completed successfully'  # TODO: Localize


def _check_and_fire(action, params=None):
    if action is not None:
        action(params)
