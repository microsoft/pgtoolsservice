# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.hosting import RequestContext


class ExecuteRequestWorkerArgs():

    def __init__(
                self,
                owner_uri: str,
                connection: 'psycopg2.extensions.connection',
                request_context: RequestContext,
                before_query_initialize=None,
                on_batch_start=None,
                on_message_notification=None,
                on_resultset_complete=None,
                on_batch_complete=None,
                on_query_complete=None
                ):

        self.owner_uri = owner_uri
        self.connection = connection
        self.request_context = request_context
        self.before_query_initialize = before_query_initialize
        self.on_batch_start = on_batch_start
        self.on_message_notification = on_message_notification
        self.on_resultset_complete = on_resultset_complete
        self.on_batch_complete = on_batch_complete
        self.on_query_complete = on_query_complete
