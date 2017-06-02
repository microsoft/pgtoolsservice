# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import logging


class QueryExecutionService(object):
    """Service for executing queries"""

    def __init__(self, server):
        logging.debug('creating query execution object')
        self.server = server

    def handle_execute_query_request(self, ownerUri, querySelection):
        logging.debug('running execute query')

        QUERY = "SELECT * from temp"
        conn = self.server.connection_service.connection
        logging.debug('Connection when attempting to query is %s', self.server.connection_service.connection)
        if conn is None:
            logging.debug('Attempted to run query without an active connection')
            return
        cur = conn.cursor()
        try:
            self.server.send_event("query/batchStart", "")  # TODO: populate and pass in a BatchSummary
            cur.execute(QUERY)
            # TODO: send responses asynchronously
            # TODO: populate and pass in a ResultSetSummary
            self.server.send_event("query/resultSetComplete", cur.fetchall())
            self.server.send_event("query/message", "")  # TODO: populate and pass in a ResultMessage
            self.server.send_event("query/batchEnd", "")  # TODO: populate and pass in a BatchSummary
            self.server.send_event("query/complete", "")  # TODO: populate and pass in a  BatchSummary
        except BaseException:
            logging.debug('Query execution failed for following query: %s', QUERY)
            return
        finally:
            cur.close()
