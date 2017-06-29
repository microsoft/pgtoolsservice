# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
import threading
from typing import Callable, Dict, List, Optional  # noqa

import psycopg2
import psycopg2.errorcodes
import sqlparse

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.query_execution.contracts import (
    EXECUTE_STRING_REQUEST, EXECUTE_DOCUMENT_SELECTION_REQUEST, ExecuteRequestParamsBase,
    BATCH_START_NOTIFICATION, BATCH_COMPLETE_NOTIFICATION, ResultSetNotificationParams,
    MESSAGE_NOTIFICATION, RESULT_SET_COMPLETE_NOTIFICATION, MessageNotificationParams,
    QUERY_COMPLETE_NOTIFICATION, SUBSET_REQUEST, ExecuteDocumentSelectionParams,
    BatchSummary, CANCEL_REQUEST, QueryCancelParams, SubsetParams
)
from pgsqltoolsservice.query_execution.contracts.common import (
    BatchEventParams, ResultMessage,
    QueryCompleteParams, SubsetResult, ResultSetSubset,
    QueryCancelResult
)
from pgsqltoolsservice.connection.contracts import ConnectionType
from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.query import Query, ExecutionState
from pgsqltoolsservice.query_execution.result_set import ResultSet
import pgsqltoolsservice.utils as utils


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

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Query execution service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_execute_query_request(
        self, request_context: RequestContext, params: ExecuteRequestParamsBase
    ) -> None:
        """Kick off thread to execute query in response to an incoming execute query request"""

        # Create a new query if one does not already exist or we already executed the previous one
        if params.owner_uri not in self.query_results or self.query_results[params.owner_uri].execution_state is ExecutionState.EXECUTED:
            self.query_results[params.owner_uri] = Query(params.owner_uri, self._get_query_text_from_execute_params(params), request_context)
        elif self.query_results[params.owner_uri].execution_state is ExecutionState.EXECUTING:
            request_context.send_error('Another query currently executing.')  # TODO: Localize
            return

        self.query_results[params.owner_uri].execution_state = ExecutionState.EXECUTING

        thread = threading.Thread(
            target=self._execute_query_request_worker,
            args=(request_context, params)
        )
        self.owner_to_thread_map[params.owner_uri] = thread
        thread.daemon = True
        thread.start()

    def _handle_subset_request(self, request_context: RequestContext, params: SubsetParams):
        """Sends a response back to the query/subset request"""
        result_set_subset = ResultSetSubset(self.query_results, params.owner_uri,
                                            params.batch_index, params.result_set_index, params.rows_start_index,
                                            params.rows_start_index + params.rows_count)
        request_context.send_response(SubsetResult(result_set_subset))

    def _handle_cancel_query_request(self, request_context: RequestContext, params: QueryCancelParams):
        """Handles a 'query/cancel' request"""
        try:
            if params.owner_uri in self.query_results:
                query = self.query_results[params.owner_uri]
            else:
                request_context.send_response(QueryCancelResult('QueryServiceRequestsNoQuery'))  # TODO: Localize
                return

            # Only cancel the query if we're in a cancellable state
            if query.execution_state is not ExecutionState.EXECUTED:
                query.is_canceled = True

            # Only need to do additional work to cancel the query
            # if it's currently running
            if query.execution_state is ExecutionState.EXECUTING:
                self.cancel_query(params.owner_uri)
            request_context.send_response(QueryCancelResult())

        except Exception as e:
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception(str(e))
            request_context.send_error('Unhandled exception: {}'.format(str(e)))  # TODO: Localize

    def cancel_query(self, owner_uri: str):
        conn = self.get_connection(owner_uri, ConnectionType.QUERY)
        cancel_conn = self.get_connection(owner_uri, ConnectionType.QUERY_CANCEL)
        if conn is None or cancel_conn is None:
            raise LookupError('Could not find associated connection')  # TODO: Localize
        backend_pid = conn.get_backend_pid()
        cur = cancel_conn.cursor()
        try:
            cur.execute("SELECT pg_cancel_backend (%s)", (backend_pid,))
        # This exception occurs when we run SELECT pg_cancel_backend on
        # a query that's currently executing
        except BaseException:
            raise

    def _execute_query_request_worker(self, request_context: RequestContext, params: ExecuteRequestParamsBase):
        """Worker method for 'handle execute query request' thread"""
        # Wrap all the work up to sending the response in a try/except block so that we can send an error if it fails
        try:
            # Initialize these in case initializing any of them raise an exception,
            # since they're all being used in our exception method
            conn = None
            cur = None
            batch = None

            query = self.query_results[params.owner_uri]
            conn = self.get_connection(params.owner_uri, ConnectionType.QUERY)
            request_context.send_response({})

        except Exception as e:
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception(
                    'Encountered exception while handling query request')  # TODO: Localize
            request_context.send_error('Unhandled exception: {}'.format(str(e)))  # TODO: Localize
            return

        try:
            # Get the cursor and start executing the query
            cur = conn.cursor()

            for batch in query.batches:
                # send query/batchStart response
                if query.is_canceled:
                    raise RuntimeError("Query canceled by user.")  # TODO: Localize
                batch_event_params = BatchEventParams(batch.build_batch_summary(), params.owner_uri)
                request_context.send_notification(BATCH_START_NOTIFICATION, batch_event_params)

                results = self.execute_query(batch.batch_text, cur, batch, params.owner_uri, request_context)

                if results is not None:
                    result_set = ResultSet(0, batch.id, cur.description, cur.rowcount, results)
                    batch.result_set = result_set

                summary = batch.build_batch_summary()

                # send query/resultSetComplete response
                # assuming only 0 or 1 result set summaries for now
                result_set_params = self.build_result_set_complete_params(summary, params.owner_uri)
                request_context.send_notification(RESULT_SET_COMPLETE_NOTIFICATION, result_set_params)

                # send query/message response
                message = self.create_message(cur)
                message_params = self.build_message_params(params.owner_uri, batch.id, message, False)
                request_context.send_notification(MESSAGE_NOTIFICATION, message_params)

                # send query/batchComplete and query/complete response
                batch_event_params = BatchEventParams(summary, params.owner_uri)
                request_context.send_notification(BATCH_COMPLETE_NOTIFICATION, batch_event_params)

            query.execution_state = ExecutionState.EXECUTED
            query_complete_params = QueryCompleteParams([summary], params.owner_uri)
            request_context.send_notification(QUERY_COMPLETE_NOTIFICATION, query_complete_params)

        except Exception as e:
            self._resolve_query_exception(e, batch.batch_text, params.owner_uri, batch,
                                          request_context, conn)
        finally:
            if cur is not None:
                cur.close()

    def get_connection(self, owner_uri: str, connection_type: ConnectionType):
        connection_service = self._service_provider._services[utils.constants.CONNECTION_SERVICE_NAME]
        if connection_service is None:
            raise LookupError('Connection service could not be found')  # TODO: Localize
        conn = connection_service.get_connection(owner_uri, connection_type)
        if conn is None:
            raise LookupError('Could not find associated connection')  # TODO: Localize
        return conn

    def build_result_set_complete_params(self, summary: BatchSummary, owner_uri: str) -> ResultSetNotificationParams:
        summaries = summary.result_set_summaries
        result_set_summary = None
        # Check if none or empty list
        if summaries:
            result_set_summary = summaries[0]
        utils.log.log_debug(self._service_provider.logger, f'result set summary is {result_set_summary}')
        return ResultSetNotificationParams(owner_uri, result_set_summary)

    def build_message_params(self, owner_uri: str, batch_id: int, message: str, is_error: bool=False):
        result_message = ResultMessage(batch_id, is_error, utils.time.get_time_str(datetime.now()), message)
        return MessageNotificationParams(owner_uri, result_message)

    def execute_query(self, query_string: str, cur, batch: Batch, owner_uri: str,
                      request_context: RequestContext) -> List[tuple]:
        """Execute query, send back notices, and add to the query execution service's query results
        :raises RuntimeError, psycopg2.DatabaseError:
        :param query: query text to be executed
        :param cur: cursor object that will be used to execute the query
        :param batch: batch that will be updated after query execution is complete
        :param owner_uri: uri of edtior where query execution request came from
        :param request_context: request context where we will send back notices
        """
        try:
            if self.query_results[owner_uri].is_canceled:
                raise RuntimeError("Batch canceled by user.")  # TODO: Localize

            # Will raise psycopg2.DatabaseError if query is invalid
            cur.execute(query_string)
        finally:
            batch.end_time = datetime.now()
            batch.has_executed = True

            # Send back notices as a separate message to avoid error coloring / highlighting of text
            notices = cur.connection.notices
            if notices:
                notice_message_params = self.build_message_params(
                    owner_uri, batch.id, ''.join(notices), False)
                request_context.send_notification(MESSAGE_NOTIFICATION, notice_message_params)
                cur.connection.notices = []

        # Fetch the results before we commit the transaction and can't access the results anymore
        if self.query_results[owner_uri].is_canceled:
            raise RuntimeError("Batch canceled by user.")  # TODO: Localize

        results = None
        if cur.description is not None:
            results = cur.fetchall()
        return results

    def _get_query_text_from_execute_params(self, params: ExecuteRequestParamsBase):
        if isinstance(params, ExecuteDocumentSelectionParams):
            workspace_service = self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME]
            selection_range = params.query_selection.to_range() if params.query_selection is not None else None
            return workspace_service.get_text(params.owner_uri, selection_range)
        else:
            # Then params must be an instance of ExecuteStringParams, which has the query as an attribute
            return params.query

    def create_message(self, cur) -> str:
        # Only add in rows affected if cursor object's rowcount is not -1.
        # rowcount is automatically -1 when an operation occurred that
        # a row count cannot be determined for or execute() was not performed
        if cur.rowcount != -1:
            return '({0} row(s) affected)'.format(cur.rowcount)  # TODO: Localize
        else:
            return 'Commands completed successfully'  # TODO: Localize

    def _resolve_query_exception(self, e: Exception, query: str, owner_uri: str, batch: Batch,
                                 request_context: RequestContext, conn):
        utils.log.log_debug(self._service_provider.logger, f'Query execution failed for following query: {query}\n {e}')
        if isinstance(e, psycopg2.DatabaseError) or isinstance(e, RuntimeError) or isinstance(e, psycopg2.extensions.QueryCanceledError):
            error_message = str(e)
        else:
            error_message = 'Unhandled exception while executing query: {}'.format(str(e))  # TODO: Localize
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception('Unhandled exception while executing query')

        # Send a message with the error to the client
        result_message_params = self.build_message_params(
            owner_uri, 0, error_message, True)
        request_context.send_notification(MESSAGE_NOTIFICATION, result_message_params)

        # Send a batch complete notification
        summary = None
        if batch is not None:
            batch.has_error = True
            batch.has_executed = True
            summary = batch.build_batch_summary()
            self.query_results[owner_uri].execution_state = ExecutionState.EXECUTED

        batch_event_params = BatchEventParams(summary, owner_uri)
        request_context.send_notification(BATCH_COMPLETE_NOTIFICATION, batch_event_params)

        # Send a query complete notification
        query_complete_params = QueryCompleteParams([summary], owner_uri)
        request_context.send_notification(QUERY_COMPLETE_NOTIFICATION, query_complete_params)

        # If there was a failure in the middle of a transaction, roll it back.
        # Note that conn.rollback() won't work since the connection is in autocommit mode
        if conn.get_transaction_status() is psycopg2.extensions.TRANSACTION_STATUS_INERROR:
            query = Query(owner_uri, 'ROLLBACK')
            query.execute(conn)


def get_batch_strings(query_string: str) -> List[str]:
    """Splits query string into a list of batch strings"""
    # TODO: Update this to actually split the strings once spliting a query into batches is in place
    return [query_string]
