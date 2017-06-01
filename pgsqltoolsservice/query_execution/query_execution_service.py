# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import psycopg2
import logging

from pgsqltoolsservice.connection_service import ConnectionService

class QueryExecutionService(object):
    """Class that executes a query"""

    def __init__(self, server):
        #TODO: Add more params
        logging.debug('creating query execution object')
        self.server = server

    def handle_execute_query_request(self, ownerUri, querySelection):
        logging.debug('running execute query')

        conn = self.server.connection_service.connection
        logging.debug('Connection when attempting to query is %s', self.server.connection_service.connection)
        if conn == None:
            logging.debug('Attempted to run query without an active connection')
            return
        cur = conn.cursor()
        try:
            self.server.send_event("query/batchStart", "") #TODO: populate and pass in a BatchSummary
            cur.execute("SELECT * from temp")
        except:
            logging.debug('Query execution failed for following query: %s', "SELECT * from postgresql")
            cur.close()
            return
        
        #TODO: send responses asynchronously
        self.server.send_event("query/resultSetComplete", cur.fetchall()) #TODO: populate and pass in a ResultSetSummary
        self.server.send_event("query/message", "") #TODO: populate and pass in a ResultMessage
        self.server.send_event("query/batchEnd", "") #TODO: populate and pass in a BatchSummary
        self.server.send_event("query/complete", "") #TODO: populate and pass in a  BatchSummary
        cur.close()

