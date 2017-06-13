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
from pgsqltoolsservice.workspace import TextRange


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
        # Retrieve the connection service
        connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
        if connection_service is None:
            raise LookupError('Connection service could not be found')  # TODO: Localize
        conn = self.get_connection(connection_service, params.owner_uri)

        # Get the query from the parameters or from the workspace service
        query = None
        if isinstance(params, ExecuteDocumentSelectionParams):
            workspace_service = self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME]
            text_range = TextRange(params.query_selection.start_line,
                                   params.query_selection.start_column,
                                   params.query_selection.end_line,
                                   params.query_selection.end_column) if params.query_selection is not None else None
            query = workspace_service.get_text(params.owner_uri, text_range)
        else:
            query = params.query
        batch_id = 0
        utils.log.log_debug(self._service_provider.logger, f'Connection when attempting to query is {conn}')
        if conn is None:
            # TODO: Send back appropriate error response
            utils.log.log_debug(self._service_provider.logger, 'Attempted to run query without an active connection')
            return

        request_context.send_response({})
        cur = conn.cursor()

        try:

            # TODO: send responses asynchronously

            # send query/batchStart response
            batch = Batch(batch_id, params.query_selection, False)
            batch_event_params = BatchEventParams(batch.build_batch_summary(), params.owner_uri)
            request_context.send_notification(BATCH_START_NOTIFICATION, batch_event_params)

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
            message = "({0} rows affected)".format(cur.rowcount)
            result_message = ResultMessage(batch_id, False, utils.time.get_time_str(datetime.now()), message)
            message_params = MessageParams(result_message, params.owner_uri)
            request_context.send_notification(MESSAGE_NOTIFICATION, message_params)

            summaries = []
            summaries.append(summary)
            query_complete_params = QueryCompleteParams(summaries, params.owner_uri)
            # send query/batchComplete and query/complete resposnes
            request_context.send_notification(BATCH_COMPLETE_NOTIFICATION, batch_event_params)
            request_context.send_notification(QUERY_COMPLETE_NOTIFICATION, query_complete_params)

        except psycopg2.DatabaseError as e:
            utils.log.log_debug(self._service_provider.logger, f'Query execution failed for following query: {query}')
            result_message = ResultMessage(
                batch_id,
                True,
                utils.time.get_time_str(datetime.now()),
                psycopg2.errorcodes.lookup(e.pgcode))
            message_params = MessageParams(result_message, params.owner_uri)
            request_context.send_notification(MESSAGE_NOTIFICATION, message_params)
            return
        finally:
            if cur is not None:
                cur.close()

    def get_connection(self, connection_service, owner_uri):
        """Get the connection string"""
        connection_info = connection_service.owner_to_connection_map[owner_uri]
        utils.log.log_debug(self._service_provider.logger, f'Connection info is {connection_info}')
        if connection_info is None:
            return None
        connection = connection_info.get_connection(ConnectionType.DEFAULT)
        utils.log.log_debug(self._service_provider.logger, f'Connection is {connection}')
        return connection

    # TODO: Analyze arguments to look for a particular subset of a particular result.
    # Currently just sending our only result
    def handle_subset_request(self, subset_params, request_context):
        pass
        # send back query results
        # subsetresult -> resultsetsubset -> {rowcount, dbcellvalue[][]}
