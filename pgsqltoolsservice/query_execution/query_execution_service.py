# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from typing import List

import psycopg2
import psycopg2.errorcodes

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.query_execution.contracts import (
    EXECUTE_STRING_REQUEST, EXECUTE_DOCUMENT_SELECTION_REQUEST, ExecuteRequestParamsBase,
    BATCH_START_NOTIFICATION, BATCH_COMPLETE_NOTIFICATION, ResultSetNotificationParams,
    MESSAGE_NOTIFICATION, RESULT_SET_COMPLETE_NOTIFICATION, MessageNotificationParams,
    QUERY_COMPLETE_NOTIFICATION, SUBSET_REQUEST, ExecuteDocumentSelectionParams
)
from pgsqltoolsservice.query_execution.contracts.common import (
    BatchEventParams, ResultMessage, DbCellValue,
    DbColumn, QueryCompleteParams, SubsetResult, ResultSetSubset
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
        self.query_results: List[List[tuple]] = []

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
        # Retrieve the connection service
        connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
        if connection_service is None:
            raise LookupError('Connection service could not be found')  # TODO: Localize
        conn = self.get_connection(connection_service, params.owner_uri)

        # Get the query from the parameters or from the workspace service
        query = self._get_query_from_execute_params(params)
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

            self.execute_query(query, cur, batch)
            if cur.description is not None:
                batch.result_sets.append(ResultSet(len(self.query_results),
                                    batch_id, cur.description, cur.rowcount))
            summary = batch.build_batch_summary()
            batch_event_params = BatchEventParams(summary, params.owner_uri)

            conn.commit()

            # send query/resultSetComplete response
            # assuming only 0 or 1 result set summaries for now
            result_set_params = self.build_result_set_complete_params(batch, params.owner_uri)
            request_context.send_notification(RESULT_SET_COMPLETE_NOTIFICATION, result_set_params)

            # send query/message response
            message = "({0} rows affected)".format(cur.rowcount)
            message_params = self.build_message_params(params.owner_uri, batch_id, message)
            request_context.send_notification(MESSAGE_NOTIFICATION, message_params)

            summaries = []
            summaries.append(summary)
            query_complete_params = QueryCompleteParams(summaries, params.owner_uri)
            # send query/batchComplete and query/complete resposnes
            request_context.send_notification(BATCH_COMPLETE_NOTIFICATION, batch_event_params)
            request_context.send_notification(QUERY_COMPLETE_NOTIFICATION, query_complete_params)

        except Exception as e:
            # TODO: On error, send error correctly and then send query complete notification
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception(f'Query {query} failed')
            result_message_params = self.build_message_params(
                params.owner_uri, batch_id, str(e))
            request_context.send_notification(MESSAGE_NOTIFICATION, result_message_params)
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

    def _handle_subset_request(self, request_context: RequestContext, params: SubsetParams):
        """Sends a response back to the query/subset request"""
        # Assume we only ever have 1 'batch' since this is PostgreSQL, so batch index is unnecessary.
        # Result_set_index starts from 1, so subtract 1 when indexing.
        result_set_subset = ResultSetSubset(self.query_results[params.result_set_index - 1], 
            params.rows_start_index, params.rows_start_index + params.rows_count)
        request_context.send_response(SubsetResult(result_set_subset))

    def build_result_set_complete_params(self, batch: Batch, owner_uri: str):
        summaries = batch.build_batch_summary().result_set_summaries
        result_set_summary = None if (summaries is None) else summaries[0]
        return ResultSetNotificationParams(owner_uri, result_set_summary)

    def build_message_params(self, owner_uri: str, batch_id: int, message: str):
        result_message = ResultMessage(batch_id, False, utils.time.get_time_str(datetime.now()), message)
        return MessageNotificationParams(owner_uri, result_message)

    def execute_query(self, query, cur, batch: Batch) -> bool:
        """Execute query and add to the query execution service's query results
        """
        cur.execute(query)
        batch.has_executed = True
        batch.end_time = datetime.now()
        utils.log.log_debug(self._service_provider.logger, f'cur.description is {cur.description}')
        if cur.description is not None:
            self.query_results.append(cur.fetchall())
    
    def _get_query_from_execute_params(self, params: ExecuteRequestParamsBase):
        if isinstance(params, ExecuteDocumentSelectionParams):
            workspace_service = self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME]
            selection_range = params.query_selection.to_range() if params.query_selection is not None else None
            return workspace_service.get_text(params.owner_uri, selection_range)
        else:
            # Then params must be an instance of ExecuteStringParams, which has the query as an attribute
            return params.query
