# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from typing import List

import psycopg2

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.query_execution.contracts import (
    EXECUTE_STRING_REQUEST, EXECUTE_DOCUMENT_SELECTION_REQUEST, ExecuteRequestParamsBase,
    BATCH_START_NOTIFICATION, BATCH_COMPLETE_NOTIFICATION, ResultSetNotificationParams,
    MESSAGE_NOTIFICATION, RESULT_SET_COMPLETE_NOTIFICATION, MessageNotificationParams,
    QUERY_COMPLETE_NOTIFICATION, SUBSET_REQUEST, SubsetNotificationParams
)
from pgsqltoolsservice.query_execution.contracts.common import (
    BatchEventParams, ResultMessage, MessageParams, DbCellValue,
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
        self.query_results = []

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
        connection_service = self._service_provider['connection']
        if connection_service is None:
            raise LookupError('Connection service could not be found')  # TODO: Localize
        conn = self.get_connection(connection_service, params.owner_uri)

        # Setup a dummy query and batch id
        query = "SELECT * from pg_authid"
        BATCH_ID = 0
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
            batch = Batch(BATCH_ID, params.query_selection, False)
            batch_event_params = BatchEventParams(batch.build_batch_summary(), params.owner_uri)
            request_context.send_notification(BATCH_START_NOTIFICATION, batch_event_params)

            cur.execute(query)
            batch.has_executed = True
            batch.end_time = datetime.now()
            self.query_results.append(cur.fetchall())

            column_info = self.generate_column_info(cur.description)
            batch.result_sets.append(ResultSet(0, 0, column_info, cur.rowcount))
            summary = batch.build_batch_summary()
            batch_event_params = BatchEventParams(summary, params.owner_uri)

            conn.commit()

            # send query/resultSetComplete response
            #assuming only 1 result set summary for now 
            result_set_summary = batch.build_batch_summary().result_set_summaries[0]
            result_set_params = ResultSetNotificationParams(params.owner_uri, result_set_summary)
            request_context.send_notification(RESULT_SET_COMPLETE_NOTIFICATION, result_set_params)

            # send query/message response
            message = "({0} rows affected)".format(cur.rowcount)
            result_message = ResultMessage(BATCH_ID, False, utils.time.get_time_str(datetime.now()), message)
            message_params = MessageNotificationParams(params.owner_uri, result_message)
            request_context.send_notification(MESSAGE_NOTIFICATION, message_params)

            summaries = []
            summaries.append(summary)
            query_complete_params = QueryCompleteParams(summaries, params.owner_uri)
            # send query/batchComplete and query/complete resposnes
            request_context.send_notification(BATCH_COMPLETE_NOTIFICATION, batch_event_params)
            request_context.send_notification(QUERY_COMPLETE_NOTIFICATION, query_complete_params)

        except psycopg2.DatabaseError as e:
            # TODO: On error, send error correctly and then send query complete notification
            utils.log.log_debug(self._service_provider.logger, f'Query execution failed for following query: {query}')
            result_message = ResultMessage(
                psycopg2.errorcodes.lookup(
                    e.pgcode), True, utils.time.get_time_str(
                    datetime.now()), BATCH_ID)
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
    def _handle_subset_request(self, request_context: RequestContext, params: SubsetParams):

        # send back query results
        if (self.query_results is None or params.batch_index < 0 or params.batch_index >= len(self.query_results) or 
          params.result_set_index < 0 or params.result_set_index >= len(self.query_results) or params.rows_start_index  < 0 or 
          params.rows_start_index + params.rows_count >= len(self.query_results[params.result_set_index]) or params.rows_count < 0):
            #TODO: error and return
            pass
        # Assume we only ever have 1 'batch' since this is PostgreSQL, so batch index is unnecessary
        db_cell_values = self.build_db_cell_values(self.query_results[params.batch_index], params.rows_start_index, params.rows_start_index + params.rows_count)
        result_set_subset = ResultSetSubset(len(db_cell_values), db_cell_values)
        request_context.send_response(SubsetResult(result_set_subset))

    def build_db_cell_values(self, results, start_index, end_index) -> List[List[DbCellValue]]:
        """ param results: a list of rows for a query result, where each row consists of tuples """
        rows = results[start_index : end_index]
        db_cell_values: List[List[DbCellValue]] = []
        row_id = start_index
        for row in rows:
            db_cell_value_row: List[DbCellValue] = []
            for cell in row:
                db_cell_value_row.append(DbCellValue(cell, cell is None, cell, row_id))
            db_cell_values.append(db_cell_value_row)
            row_id += 1
        return db_cell_values

    def generate_column_info(self, description):
        column_info = []
        index = 0
        for desc in description:
            column_info.append(DbColumn(index, desc))
            index += 1
        return column_info


