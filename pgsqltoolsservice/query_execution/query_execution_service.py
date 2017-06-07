# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import psycopg2
import logging
import jsonpickle

from pgsqltoolsservice.connection_service import ConnectionService
from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.selection_data import SelectionData
from pgsqltoolsservice.query_execution.batch_event_params import BatchEventParams
from pgsqltoolsservice.query_execution.result_message import ResultMessage
from pgsqltoolsservice.query_execution.message_params import MessageParams
from pgsqltoolsservice.query_execution.db_column import DbColumn

class QueryExecutionService(object):
    """Class that executes a query"""

    def __init__(self, server):
        #TODO: Add more params
        logging.debug('creating query execution object')
        self.server = server

    def handle_execute_query_request(self, ownerUri, querySelection):
        logging.debug('running execute query')
        #TODO: Hook up to workspace service so that we can get the actual query text
        QUERY = "SELECT * from pg_authid"
        BATCH_ID = 0
        conn = self.server.connection_service.connection
        logging.debug('Connection when attempting to query is %s', self.server.connection_service.connection)
        if conn is None:
            logging.debug('Attempted to run query without an active connection')
            return
        cur = conn.cursor()
        try:
            #TODO: send responses asynchronously
            batch = Batch(BATCH_ID, querySelection, False)
            batch_event_params = BatchEventParams(batch.build_batch_summary, ownerUri)
            json_batch_params = jsonpickle.encode(batch_event_params, unpicklable = False)
            self.server.send_event("query/batchStart", json_batch_params)
            cur.execute(QUERY)

            #TODO: update dbcolumn wrapper constructor / rename the class
            column_info = []
            index = 0
            for desc in cur.description:
                column_info.append(DbColumn(index, desc))
                index += 1
            
            self.server.send_event("query/resultSetComplete", cur.fetchall()) #TODO: populate and pass in a ResultSetSummary

            message = "({0} rows affected)".format(cur.rowcount)
            result_message = ResultMessage(message, False, BATCH_ID)
            message_params = MessageParams(result_message, ownerUri)
            self.server.send_event("query/message", message_params)

            self.server.send_event("query/batchEnd", "") #TODO: populate and pass in a BatchSummary
            self.server.send_event("query/complete", "") #TODO: populate and pass in a  BatchSummary
        except psycopg2.DatabaseError as e:
            logging.debug('Query execution failed for following query: %s', QUERY) 
            result_message = ResultMessage(psycopg2.errorcodes.lookup(e.pgcode), True, BATCH_ID)
        finally:
            cur.close()

