# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime

import psycopg2
import psycopg2.errorcodes

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.query_execution.contracts import (
    EXECUTE_STRING_REQUEST, EXECUTE_DOCUMENT_SELECTION_REQUEST,
    ExecuteRequestParamsBase, ExecuteDocumentSelectionParams,
    BATCH_START_NOTIFICATION, BATCH_COMPLETE_NOTIFICATION,
    MESSAGE_NOTIFICATION,
    QUERY_COMPLETE_NOTIFICATION,
)
from pgsqltoolsservice.query_execution.contracts.common import (
    BatchEventParams, ResultMessage, MessageParams, DbColumn, QueryCompleteParams
)
from pgsqltoolsservice.connection.contracts import ConnectionType
from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.result_set import ResultSet
import pgsqltoolsservice.utils as utils


class QueryExecutionService(object):
    """Service for executing queries"""

    def __init__(self):
        self._service_provider: ServiceProvider = None

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(
            EXECUTE_STRING_REQUEST, self._handle_execute_query_request
        )
        self._service_provider.server.set_request_handler(
            EXECUTE_DOCUMENT_SELECTION_REQUEST, self._handle_execute_query_request
        )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Query execution service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_execute_query_request(
        self, request_context: RequestContext, params: ExecuteRequestParamsBase
    ) -> None:
        # Wrap all the work up to sending the response in a try/except block so that we can send an error if it fails
        try:
            # Retrieve the connection service
            connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
            conn = connection_service.get_connection(params.owner_uri, ConnectionType.DEFAULT)

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

            # TODO: send responses asynchronously
            cur.execute(query)
            batch.has_executed = True
            batch.end_time = datetime.now()
            self.query_results = cur.fetchall()

            column_info = []
            index = 0
            for desc in cur.description:
                column_info.append(DbColumn(index, desc))
                index += 1
            batch.result_sets.append(ResultSet(0, 0, column_info, cur.rowcount))
            summary = batch.build_batch_summary()
            batch_event_params = BatchEventParams(summary, params.owner_uri)

            conn.commit()

            # send query/resultSetComplete response
            # result_set_summary = batch.build_batch_summary().result_set_summaries
            # result_set_event_params = ResultSetEventParams(result_set_summary, params.owner_uri)
            # self.server.send_event("query/resultSetComplete", result_set_event_params)

            # send query/message response
            message = "({0} rows affected)".format(cur.rowcount)  # TODO: Localize
            result_message = ResultMessage(batch_id, False, utils.time.get_time_str(datetime.now()), message)
            message_params = MessageParams(result_message, params.owner_uri)
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
            result_message = ResultMessage(
                batch_id,
                True,
                utils.time.get_time_str(datetime.now()),
                error_message)
            message_params = MessageParams(result_message, params.owner_uri)
            request_context.send_notification(MESSAGE_NOTIFICATION, message_params)

            # Send a batch complete notification
            batch.has_executed = True
            batch.has_error = True
            batch.end_time = datetime.now()
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

    # TODO: Analyze arguments to look for a particular subset of a particular result.
    # Currently just sending our only result
    def handle_subset_request(self, subset_params, request_context):
        pass
        # send back query results
        # subsetresult -> resultsetsubset -> {rowcount, dbcellvalue[][]}

    def _get_query_from_execute_params(self, params: ExecuteRequestParamsBase):
        if isinstance(params, ExecuteDocumentSelectionParams):
            workspace_service = self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME]
            selection_range = params.query_selection.to_range() if params.query_selection is not None else None
            return workspace_service.get_text(params.owner_uri, selection_range)
        else:
            # Then params must be an instance of ExecuteStringParams, which has the query as an attribute
            return params.query
