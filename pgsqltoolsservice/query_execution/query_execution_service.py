# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
import threading
import uuid
from typing import Callable, Dict, List, Optional  # noqa

import psycopg2
import psycopg2.errorcodes

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.query_execution.contracts import (
    EXECUTE_STRING_REQUEST, EXECUTE_DOCUMENT_SELECTION_REQUEST, ExecuteRequestParamsBase,
    BATCH_START_NOTIFICATION, BATCH_COMPLETE_NOTIFICATION, ResultSetNotificationParams,
    MESSAGE_NOTIFICATION, RESULT_SET_COMPLETE_NOTIFICATION, MessageNotificationParams,
    QUERY_COMPLETE_NOTIFICATION, SUBSET_REQUEST, ExecuteDocumentSelectionParams,
    BatchSummary, CANCEL_REQUEST, QueryCancelParams, SubsetParams,
    BatchNotificationParams, QueryCompleteNotificationParams, QueryDisposeParams,
    DISPOSE_REQUEST, SIMPLE_EXECUTE_REQUEST, SimpleExecuteRequest, ExecuteStringParams,
    SimpleExecuteResponse
)
from pgsqltoolsservice.connection.contracts import ConnectRequestParams
from pgsqltoolsservice.query_execution.contracts.common import (
    ResultMessage, SubsetResult, ResultSetSubset, QueryCancelResult
)
from pgsqltoolsservice.connection.contracts import ConnectionType
from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.query import ExecutionState, Query
import pgsqltoolsservice.utils as utils


CANCELATION_QUERY = 'SELECT pg_cancel_backend (%s)'
NO_QUERY_MESSAGE = 'QueryServiceRequestsNoQuery'


class ExecuteRequestWorkerArgs():

    def __init__(self, owner_uri: str, connection: 'psycopg2.extensions.connection', request_context: RequestContext,
                 before_query_initialize: Callable=None, on_batch_start: Callable=None, on_message_notification: Callable=None,
                 on_resultset_complete: Callable=None, on_batch_complete: Callable=None, on_query_complete: Callable=None):

        self.owner_uri = owner_uri
        self.connection = connection
        self.request_context = request_context
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

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider
        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(
            EXECUTE_STRING_REQUEST, self._handle_execute_query_request
        )
        self._service_provider.server.set_request_handler(
            EXECUTE_DOCUMENT_SELECTION_REQUEST, self._handle_execute_query_request
        )

        self._service_provider.server.set_request_handler(
            SUBSET_REQUEST, self._handle_subset_request
        )

        self._service_provider.server.set_request_handler(
            CANCEL_REQUEST, self._handle_cancel_query_request
        )

        self._service_provider.server.set_request_handler(
            SIMPLE_EXECUTE_REQUEST, self._handle_simple_execute_request
        )

        self._service_provider.server.set_request_handler(
            DISPOSE_REQUEST, self._handle_dispose_request
        )
        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Query execution service successfully initialized')

    # REQUEST HANDLERS #####################################################
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

        worker_args = ExecuteRequestWorkerArgs(new_owner_uri, new_connection, request_context, on_query_complete=on_query_complete)

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

        worker_args = ExecuteRequestWorkerArgs(params.owner_uri, conn, request_context, before_query_initialize,
                                               on_batch_start, on_message_notification, on_resultset_complete,
                                               on_batch_complete, on_query_complete)

        self._start_query_execution_thread(request_context, params, worker_args)

    def _start_query_execution_thread(self, request_context: RequestContext, params: ExecuteRequestParamsBase, worker_args: ExecuteRequestWorkerArgs= None):

        # Create a new query if one does not already exist or we already executed the previous one
        if params.owner_uri not in self.query_results or self.query_results[params.owner_uri].execution_state is ExecutionState.EXECUTED:
            self.query_results[params.owner_uri] = Query(params.owner_uri, self._get_query_text_from_execute_params(params))
        elif self.query_results[params.owner_uri].execution_state is ExecutionState.EXECUTING:
            request_context.send_error('Another query is currently executing.')  # TODO: Localize
            return

        self.query_results[params.owner_uri].execution_state = ExecutionState.EXECUTING

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
        result_set_subset = ResultSetSubset(self.query_results, params.owner_uri,
                                            params.batch_index, params.result_set_index, params.rows_start_index,
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
        backend_pid = conn.get_backend_pid()
        cur = cancel_conn.cursor()
        try:
            cur.execute(CANCELATION_QUERY, (backend_pid,))
        # This exception occurs when we run SELECT pg_cancel_backend on
        # a query that's currently executing
        except BaseException:
            raise

    def _execute_query_request_worker(self, worker_args: ExecuteRequestWorkerArgs):
        """Worker method for 'handle execute query request' thread"""

        _check_and_fire(worker_args.before_query_initialize, {})

        # Set up batch execution callback methods for sending notifications
        def _batch_execution_started_callback(query: Query, batch: Batch) -> None:
            batch_event_params = BatchNotificationParams(batch.build_batch_summary(), worker_args.owner_uri)
            _check_and_fire(worker_args.on_batch_start, batch_event_params)

        def _batch_execution_finished_callback(query: Query, batch: Batch) -> None:
            # Send back notices as a separate message to avoid error coloring / highlighting of text
            notices = batch.notices
            if notices:
                notice_message_params = self.build_message_params(query.owner_uri, batch.id, ''.join(notices), False)
                _check_and_fire(worker_args.on_message_notification, notice_message_params)
                batch.notices = []

            batch_summary = batch.build_batch_summary()

            # send query/resultSetComplete response
            result_set_params = self.build_result_set_complete_params(batch_summary, query.owner_uri)
            _check_and_fire(worker_args.on_resultset_complete, result_set_params)

            # If the batch was successful, send a message to the client
            if not batch.has_error:
                rows_message = _create_rows_affected_message(batch)
                message_params = self.build_message_params(query.owner_uri, batch.id, rows_message, False)
                _check_and_fire(worker_args.on_message_notification, message_params)

            # send query/batchComplete and query/complete response
            batch_event_params = BatchNotificationParams(batch_summary, worker_args.owner_uri)
            _check_and_fire(worker_args.on_batch_complete, batch_event_params)

        query = self.query_results[worker_args.owner_uri]

        # Wrap execution in a try/except block so that we can send an error if it fails
        try:
            query.execute(worker_args.connection, _batch_execution_started_callback, _batch_execution_finished_callback)
        except Exception as e:
            self._resolve_query_exception(e, query, worker_args.request_context, worker_args.connection)
        finally:
            # Send a query complete notification
            batch_summaries = [batch.build_batch_summary() for batch in query.batches]
            query_complete_params = QueryCompleteNotificationParams(worker_args.owner_uri, batch_summaries)
            _check_and_fire(worker_args.on_query_complete, query_complete_params)

    def _get_connection(self, owner_uri: str, connection_type: ConnectionType) -> 'psycopg2.connection':
        """
        Get a connection for the given owner URI and connection type from the connection service

        :param owner_uri: the URI to get the connection for
        :param connection_type: the type of connection to get
        :returns: a psycopg2 connection
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

    def build_message_params(self, owner_uri: str, batch_id: int, message: str, is_error: bool=False):
        result_message = ResultMessage(batch_id, is_error, utils.time.get_time_str(datetime.now()), message)
        return MessageNotificationParams(owner_uri, result_message)

    def _get_query_text_from_execute_params(self, params: ExecuteRequestParamsBase):
        if isinstance(params, ExecuteDocumentSelectionParams):
            workspace_service = self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME]
            selection_range = params.query_selection.to_range() if params.query_selection is not None else None
            return workspace_service.get_text(params.owner_uri, selection_range)
        else:
            # Then params must be an instance of ExecuteStringParams, which has the query as an attribute
            return params.query

    def _resolve_query_exception(self, e: Exception, query: Query, request_context: RequestContext, conn: 'psycopg2.connection', is_rollback_error=False):
        utils.log.log_debug(self._service_provider.logger, f'Query execution failed for following query: {query.query_text}\n {e}')
        if isinstance(e, psycopg2.DatabaseError) or isinstance(e, RuntimeError) or isinstance(e, psycopg2.extensions.QueryCanceledError):
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
        request_context.send_notification(MESSAGE_NOTIFICATION, result_message_params)

        # If there was a failure in the middle of a transaction, roll it back.
        # Note that conn.rollback() won't work since the connection is in autocommit mode
        if not is_rollback_error and conn.get_transaction_status() is psycopg2.extensions.TRANSACTION_STATUS_INERROR:
            rollback_query = Query(query.owner_uri, 'ROLLBACK')
            try:
                rollback_query.execute(conn)
            except Exception as rollback_exception:
                # If the rollback failed, handle the error as usual but don't try to roll back again
                self._resolve_query_exception(rollback_exception, rollback_query, request_context, conn, True)


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
