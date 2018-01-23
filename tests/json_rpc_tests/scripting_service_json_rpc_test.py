# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import psycopg2

from pgsqltoolsservice.hosting.json_message import JSONRPCMessageType
from tests.integration import get_connection_details, create_extra_test_database
from tests.json_rpc_tests import JSONRPCTestCase, DefaultRPCTestMessages, RPCTestMessage
from tests.json_rpc_tests.object_explorer_test_metadata import META_DATA, CREATE_SCRIPTS, GET_OID_SCRIPTS
from tests.json_rpc_tests.scripting_service_test_metadata import SCRIPT_META_DATA


class ScriptingJSONRPCTests:

    # The parameter list of generated test function. It's needed when fire a function scripting request.
    CREATED_FUNCTION_PARAMETER_LIST = '(x integer, y integer, OUT sum integer)'

    def test_scripting(self):
        connection_details = get_connection_details()
        connection = psycopg2.connect(**connection_details)
        connection.autocommit = True

        args = self.create_database_objects(META_DATA, connection)

        created_object_names = {}

        for key, value in args.items():
            if key[-5:] == "_Name":
                created_object_names[key] = value

        owner_uri = 'test_uri'
        connection_details['dbname'] = args["Databases_Name"]
        connection_messages = DefaultRPCTestMessages.connection_request(owner_uri, connection_details)
        test_messages = [connection_messages[0], connection_messages[1]]

        def generate_scripting_requests(metadata):
            scripting_requests = []

            for key, metadata_value in metadata.items():
                for operation in metadata_value:
                    scripting_object = {}
                    scripting_object['name'] = created_object_names[key + 's_Name']
                    if key == 'Function':
                        scripting_object['name'] = created_object_names[key + 's_Name'] + ScriptingJSONRPCTests.CREATED_FUNCTION_PARAMETER_LIST
                    scripting_object['schema'] = 'public' if key in ['Table', 'View', 'Function'] else None
                    scripting_object['type'] = key

                    scripting_objects = [scripting_object]

                    params = {}
                    params['connectionString'] = None
                    params['filePath'] = None
                    params['scriptingObjects'] = scripting_objects
                    params['scriptDestination'] = 'ToEditor'
                    params['includeObjectCriteria'] = None
                    params['excludeObjectCriteria'] = None
                    params['includeSchemas'] = None
                    params['excludeSchemas'] = None
                    params['includeTypes'] = None
                    params['excludeTypes'] = None
                    params['scriptOptions'] = None
                    params['connectionDetails'] = None
                    params['ownerURI'] = 'test_uri'
                    params['operation'] = operation.value

                    scripting_request = RPCTestMessage(
                        'scripting/script',
                        json.dumps(params),
                        JSONRPCMessageType.Request,
                        response_verifier=lambda response: self.assertIsNotNone(response['result']['script']),
                        notification_verifiers=None)

                    scripting_requests.append(scripting_request)

            return scripting_requests

        # create requests based on metadata:
        scripting_requests = generate_scripting_requests(SCRIPT_META_DATA)

        test_messages += scripting_requests

        JSONRPCTestCase(test_messages).run()

    def create_database_objects(self, metadata: dict, connection: 'psycopg2.connection', **kwargs):

        for key, metadata_value in metadata.items():
            create_script: str = CREATE_SCRIPTS.get(key)
            if create_script is not None:
                kwargs[key + '_Name'] = metadata_value['Name']

                if key == 'Databases':
                    dbname = create_extra_test_database()
                    metadata_value['Name'] = dbname
                    kwargs[key + '_Name'] = dbname
                    connection_details = get_connection_details()
                    connection_details['dbname'] = dbname
                    connection = psycopg2.connect(**connection_details)
                    connection.autocommit = True
                else:
                    self.execute_script(create_script.format(**kwargs), connection)

                get_oid_script = GET_OID_SCRIPTS.get(key)

                if get_oid_script is not None:
                    cursor = self.execute_script(get_oid_script.format(**kwargs), connection)
                    kwargs[key + '_OID'] = cursor.fetchone()[0]

            children = metadata_value.get('Children')

            if children is not None:
                object_names = self.create_database_objects(children, connection, **kwargs)
                kwargs.update(object_names)

        return kwargs

    def execute_script(self, script: str, connection: 'psycopg2.connection'):
        cursor = connection.cursor()
        cursor.execute(script)
        return cursor
