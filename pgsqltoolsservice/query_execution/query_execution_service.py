# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.query_execution.contracts import (
    EXECUTE_STRING_REQUEST, EXECUTE_DOCUMENT_SELECTION_REQUEST, ExecuteRequestParamsBase,
    BATCH_START_NOTIFICATION, BATCH_COMPLETE_NOTIFICATION, BatchNotificationParams,
    MESSAGE_NOTIFICATION, MessageNotificationParams,
    QUERY_COMPLETE_NOTIFICATION, QueryCompleteNotificationParams,
    RESULT_SET_COMPLETE_NOTIFICATION, ResultSetNotificationParams
)


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
        connection_service = self._service_provider.get_service('connection')
        if connection_service is None:
            raise LookupError('Connection service could not be found')  # TODO: Localize
        conn = connection_service._connection   # TODO: Temporary until connection service provides better API

        # Setup a dummy query
        query = "SELECT * from temp"
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
            # TODO: send responses asynchronously
            # TODO: populate and pass in a ResultSetSummary
            request_context.send_notification(RESULT_SET_COMPLETE_NOTIFICATION, cur.fetchall())
            request_context.send_notification(MESSAGE_NOTIFICATION, "")  # TODO: populate and pass in a ResultMessage
            request_context.send_notification(BATCH_COMPLETE_NOTIFICATION, "")  # TODO: populate and pass BatchSummary
            request_context.send_notification(QUERY_COMPLETE_NOTIFICATION, "")  # TODO: populate and pass BatchSummaries
        except BaseException:
            if self._service_provider.logger is not None:
                self._service_provider.logger.debug('Query execution failed for following query: %s', query)
            return
        finally:
            cur.close()
