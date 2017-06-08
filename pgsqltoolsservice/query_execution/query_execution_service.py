# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import psycopg2
from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.query_execution.contracts import (
    EXECUTE_STRING_REQUEST, EXECUTE_DOCUMENT_SELECTION_REQUEST, ExecuteRequestParamsBase,
    BATCH_START_NOTIFICATION, BATCH_COMPLETE_NOTIFICATION,
    MESSAGE_NOTIFICATION,
    QUERY_COMPLETE_NOTIFICATION,
    RESULT_SET_COMPLETE_NOTIFICATION,
)
from pgsqltoolsservice.query_execution.contracts.common import (
    BatchEventParams, ResultMessage, MessageParams,
    DbColumn, ResultSetEventParams
)
from pgsqltoolsservice.connection.contracts import ConnectionType
from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.result_set import ResultSet

from datetime import datetime

class QueryExecutionService(object):
    """Class that executes a query"""

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
        connection_service = self._service_provider['connection']
        if connection_service is None:
            raise LookupError('Connection service could not be found')  # TODO: Localize
        conn = self.get_connection(connection_service, params.owner_uri)

        # Setup a dummy query and batch id
        query = "SELECT * from pg_authid"
        BATCH_ID = 0
        if self._service_provider.logger is not None:
            self._service_provider.logger.debug('Connection when attempting to query is %s', conn)
        if conn is None:
            if self._service_provider.logger is not None:
                self._service_provider.logger.debug('Attempted to run query without an active connection')
            return
        cur = conn.cursor()

        try:
            request_context.send_notification(BATCH_START_NOTIFICATION, "")  # TODO: populate and pass in a BatchSummary
            cur.execute(query)
            #TODO: send responses asynchronously

            #send query/batchStart response
            batch = Batch(BATCH_ID, params.query_selection, False)
            batch_event_params = BatchEventParams(batch.build_batch_summary(), params.owner_uri)
            request_context.send_notification(BATCH_START_NOTIFICATION, batch_event_params)

            cur.execute(query)
            self.query_results = cur.fetchall()

            column_info = []
            index = 0
            for desc in cur.description:
                column_info.append(DbColumn(index, desc))
                index += 1
            batch.result_sets.append(ResultSet(0 , 0, column_info, cur.rowcount))
            batch.hasExecuted = True
            batch_event_params = BatchEventParams(batch.build_batch_summary(), params.owner_uri)

            #send query/resultSetComplete response
            result_set_summary = batch.build_batch_summary().result_set_summaries
            result_set_event_params = ResultSetEventParams(result_set_summary, params.owner_uri)
            #self.server.send_event("query/resultSetComplete", result_set_event_params)

            #send query/message response
            message = "({0} rows affected)".format(cur.rowcount)
            result_message = ResultMessage(message, False, datetime.now(), BATCH_ID)
            message_params = MessageParams(result_message, params.owner_uri)
            request_context.send_notification(MESSAGE_NOTIFICATION, message_params)

            #send query/batchComplete and query/complete resposnes
            request_context.send_notification(BATCH_COMPLETE_NOTIFICATION, batch_event_params)
            request_context.send_notification(QUERY_COMPLETE_NOTIFICATION, batch_event_params)

        except psycopg2.DatabaseError as e:
            if self._service_provider.logger is not None:
                self._service_provider.logger.debug('Query execution failed for following query: %s', query) 
            result_message = ResultMessage(psycopg2.errorcodes.lookup(e.pgcode), True, datetime.now(), BATCH_ID)
            request_context.send_notification(MESSAGE_NOTIFICATION, message_params)
            return
        finally:
            cur.close()
    
    def get_connection(self, connection_service, owner_uri):
        """Get the connection string"""
        connection_info = connection_service.owner_to_map[owner_uri]
        if connection_info is None:
            return None
        return connection_info.get_connection(ConnectionType.DEFAULT)

    #TODO: Analyze arguments to look for a particular subset of a particular result.
    # Currently just sending our only result
    def handle_subset_request(self, subset_params, request_context):
        pass
            #send back query results
            # subsetresult -> resultsetsubset -> {rowcount, dbcellvalue[][]}

