# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from typing import List, Dict  # noqa

import psycopg2
import psycopg2.errorcodes

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.query_execution.contracts import (
    EXECUTE_STRING_REQUEST, EXECUTE_DOCUMENT_SELECTION_REQUEST, ExecuteRequestParamsBase,
    BATCH_START_NOTIFICATION, BATCH_COMPLETE_NOTIFICATION, ResultSetNotificationParams,
    MESSAGE_NOTIFICATION, RESULT_SET_COMPLETE_NOTIFICATION, MessageNotificationParams,
    QUERY_COMPLETE_NOTIFICATION, SUBSET_REQUEST, ExecuteDocumentSelectionParams,
    BatchSummary
)
from pgsqltoolsservice.query_execution.contracts.common import (
    BatchEventParams, ResultMessage,
    QueryCompleteParams, SubsetResult, ResultSetSubset
)
from pgsqltoolsservice.connection.contracts import ConnectionType
from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.result_set import ResultSet
from pgsqltoolsservice.query_execution.contracts.execute_request import SubsetParams
import pgsqltoolsservice.utils as utils


class QueryExecutionService(object):
    """Service for executing queries"""

    def __init__(self):
        self._service_provider: ServiceProvider = None
        # Dictionary mapping uri to a list of batches
        self.query_results: Dict[str, List[Batch]] = {}

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

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Query execution service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_execute_query_request(
        self, request_context: RequestContext, params: ExecuteRequestParamsBase
    ) -> None:

        self.query_results[params.owner_uri] = []
        # Wrap all the work up to sending the response in a try/except block so that we can send an error if it fails
        try:
            # Retrieve the connection service
            connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
            if connection_service is None:
                raise LookupError('Connection service could not be found')  # TODO: Localize
            conn = connection_service.get_connection(params.owner_uri, ConnectionType.QUERY)

            # Get the query from the parameters or from the workspace service
            query = self._get_query_from_execute_params(params)
            batch_id = 0
            utils.log.log_debug(self._service_provider.logger, f'Connection when attempting to query is {conn}')
            request_context.send_response({})
        except Exception as e:
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception('Encountered exception while handling query request')
            request_context.send_error('Unhandled exception: {}'.format(str(e)))  # TODO: Localize
            return

        try:
            # Get the cursor and start executing the query
            cur = conn.cursor()

            # send query/batchStart response
            batch = Batch(batch_id,
                          params.query_selection if isinstance(params, ExecuteDocumentSelectionParams) else None,
                          False)
            batch_event_params = BatchEventParams(batch.build_batch_summary(), params.owner_uri)
            request_context.send_notification(BATCH_START_NOTIFICATION, batch_event_params)
            results = self.execute_query(query, cur, batch)
            if results is not None:
                result_set = ResultSet(len(self.query_results[params.owner_uri]),
                                       batch_id, cur.description, cur.rowcount, results)
                batch.result_sets.append(result_set)

            summary = batch.build_batch_summary()
            batch_event_params = BatchEventParams(summary, params.owner_uri)

            conn.commit()
            self.query_results[params.owner_uri].append(batch)

            # send query/resultSetComplete response
            # assuming only 0 or 1 result set summaries for now
            result_set_params = self.build_result_set_complete_params(summary, params.owner_uri)
            request_context.send_notification(RESULT_SET_COMPLETE_NOTIFICATION, result_set_params)

            # send query/message response
            if summary.result_set_summaries:
                message = "({0} rows affected)".format(cur.rowcount)
            else:
                message = ""
            message_params = self.build_message_params(params.owner_uri, batch_id, message)
            request_context.send_notification(MESSAGE_NOTIFICATION, message_params)

            summaries = []
            summaries.append(summary)
            query_complete_params = QueryCompleteParams(summaries, params.owner_uri)
            # send query/batchComplete and query/complete resposnes
            request_context.send_notification(BATCH_COMPLETE_NOTIFICATION, batch_event_params)
            request_context.send_notification(QUERY_COMPLETE_NOTIFICATION, query_complete_params)

        except Exception as e:
            utils.log.log_debug(self._service_provider.logger, f'Query execution failed for following query: {query}')
            if isinstance(e, psycopg2.DatabaseError):
                error_message = str(e)
            else:
                error_message = 'Unhandled exception while executing query: {}'.format(str(e))  # TODO: Localize
                if self._service_provider.logger is not None:
                    self._service_provider.logger.exception('Unhandled exception while executing query')

            # Send a message with the error to the client
            result_message_params = self.build_message_params(
                params.owner_uri, batch_id, error_message, True)
            request_context.send_notification(MESSAGE_NOTIFICATION, result_message_params)

            # Send a batch complete notification
            batch.has_error = True
            summary = batch.build_batch_summary()
            batch_event_params = BatchEventParams(summary, params.owner_uri)
            request_context.send_notification(BATCH_COMPLETE_NOTIFICATION, batch_event_params)

            # Send a query complete notification
            query_complete_params = QueryCompleteParams([summary], params.owner_uri)
            request_context.send_notification(QUERY_COMPLETE_NOTIFICATION, query_complete_params)

            # Roll back the transaction if the connection is still open
            if not conn.closed:
                conn.rollback()
        finally:
            if cur is not None:
                cur.close()

    def _handle_subset_request(self, request_context: RequestContext, params: SubsetParams):
        """Sends a response back to the query/subset request"""

        result_set_subset = ResultSetSubset(self.query_results, params.owner_uri,
                                            params.batch_index, params.result_set_index, params.rows_start_index,
                                            params.rows_start_index + params.rows_count)
        request_context.send_response(SubsetResult(result_set_subset))

    def build_result_set_complete_params(self, summary: BatchSummary, owner_uri: str):
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

    def execute_query(self, query: str, cur, batch: Batch) -> bool:
        """Execute query and add to the query execution service's query results
        :raises psycopg2.DatabaseError:
        :param query: query text to be executed
        :param cur: cursor object that will be used to execute the query
        :param batch: batch that will be updated after query execution is complete
        """
        try:
            cur.execute(query)
        except Exception:
            raise
        finally:
            batch.has_executed = True
            batch.end_time = datetime.now()

        if cur.description is not None:
            return cur.fetchall()
        return None

    def _get_query_from_execute_params(self, params: ExecuteRequestParamsBase):
        if isinstance(params, ExecuteDocumentSelectionParams):
            workspace_service = self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME]
            selection_range = params.query_selection.to_range() if params.query_selection is not None else None
            return workspace_service.get_text(params.owner_uri, selection_range)
        else:
            # Then params must be an instance of ExecuteStringParams, which has the query as an attribute
            return params.query
