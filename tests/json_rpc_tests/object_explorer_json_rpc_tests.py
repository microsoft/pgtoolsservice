# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import functools
import json
import unittest
from urllib.parse import quote

import psycopg

from ossdbtoolsservice.hosting.json_message import JSONRPCMessageType
from tests.integration import (
    create_extra_test_database,
    get_connection_details,
    integration_test,
)
from tests.json_rpc_tests import DefaultRPCTestMessages, JSONRPCTestCase, RPCTestMessage
from tests.json_rpc_tests.object_explorer_test_metadata import (
    CREATE_SCRIPTS,
    GET_OID_SCRIPTS,
    META_DATA,
)


class ObjectExplorerJSONRPCTests(unittest.TestCase):
    @integration_test
    def test_object_explorer(self):
        connection_details = get_connection_details()
        connection = psycopg.connect(**connection_details)
        connection.autocommit = True

        self.args = self.create_database_objects(META_DATA, connection)

        owner_uri = "test_uri"
        connection_details["dbname"] = self.args["Databases_Name"]
        connection_messages = DefaultRPCTestMessages.connection_request(
            owner_uri, connection_details
        )
        test_messages = [connection_messages[0], connection_messages[1]]

        expected_session_id = (
            f"objectexplorer://{quote(connection_details['user'])}"
            + f"@{quote(connection_details['host'])}:{connection_details['port']}:{quote(connection_details['dbname'])}/"
        )

        def session_created_verifier(notification):
            params = notification["params"]
            self.assertIsNone(params["errorMessage"])
            self.assertTrue(params["success"])
            self.assertIn("rootNode", params)
            root_node = params["rootNode"]
            self.assertEqual(root_node["label"], connection_details["dbname"])
            self.assertEqual(root_node["nodeType"], "Database")
            self.assertIn("metadata", root_node)
            metadata = root_node["metadata"]
            self.assertEqual(metadata["metadataTypeName"], "Database")
            self.assertEqual(metadata["name"], connection_details["dbname"])

        create_session_request = RPCTestMessage(
            "objectexplorer/createsession",
            f'{{"options":{json.dumps(connection_details)}}}',
            JSONRPCMessageType.Request,
            response_verifier=lambda response: self.assertEqual(
                response["result"]["sessionId"], expected_session_id
            ),
            notification_verifiers=[
                (
                    lambda notification: notification["method"]
                    == "objectexplorer/sessioncreated",
                    session_created_verifier,
                )
            ],
        )

        def expand_completed_verifier(
            node_path, expected_nodes, exact_node_match, notification
        ):
            params = notification["params"]
            self.assertIsNone(params["errorMessage"])
            self.assertEqual(params["nodePath"], node_path)
            nodes = params["nodes"]
            self.assertGreater(len(nodes), 0)
            found_nodes = set()
            for node in nodes:
                self.assertIsNone(node["errorMessage"])
                found_nodes.add(node["label"])
            if exact_node_match:
                self.assertEqual(found_nodes, expected_nodes)
            else:
                for node in expected_nodes:
                    self.assertIn(node, found_nodes)

        def create_expand_test_message(node_path, expected_nodes, exact_node_match):
            return RPCTestMessage(
                "objectexplorer/expand",
                f'{{"sessionId":"{expected_session_id}","nodePath":"{node_path}"}}',
                JSONRPCMessageType.Request,
                response_verifier=lambda response: self.assertTrue(response["result"]),
                notification_verifiers=[
                    (
                        lambda notification: notification["method"]
                        == "objectexplorer/expandCompleted"
                        and notification["params"]["nodePath"] == node_path,
                        functools.partial(
                            expand_completed_verifier,
                            node_path,
                            expected_nodes,
                            exact_node_match,
                        ),
                    )
                ],
            )

        test_messages += [create_session_request]

        self.create_expand_messages(
            META_DATA, "/{0}/", create_expand_test_message, test_messages, **self.args
        )

        JSONRPCTestCase(test_messages).run()

        # Delete the created test role
        role_name = self.args["Roles_Name"]
        self.delete_role(connection, role_name)
        connection.close()

    def create_database_objects(
        self, meta_data: dict, connection: "psycopg.Connection", **kwargs
    ):
        for key, metadata_value in meta_data.items():
            create_script: str = CREATE_SCRIPTS.get(key)
            if create_script is not None:
                kwargs[key + "_Name"] = metadata_value["Name"]

                if key == "Databases":
                    dbname = create_extra_test_database()
                    metadata_value["Name"] = dbname
                    kwargs[key + "_Name"] = dbname
                    connection_details = get_connection_details()
                    connection_details["dbname"] = dbname
                    connection = psycopg.connect(**connection_details)
                    connection.autocommit = True
                else:
                    self.execute_script(create_script.format(**kwargs), connection)

                get_oid_script = GET_OID_SCRIPTS.get(key)

                if get_oid_script is not None:
                    cursor = self.execute_script(get_oid_script.format(**kwargs), connection)
                    kwargs[key + "_OID"] = cursor.fetchone()[0]

            children = metadata_value.get("Children")

            if children is not None:
                self.create_database_objects(children, connection, **kwargs)

        return kwargs

    def create_expand_messages(
        self, metadata, node_template, create_expand_test_message, messages, **kwargs
    ):
        for key, metadata_value in metadata.items():
            node = node_template.format(key.lower())
            object_name = self.get_object_name(
                key, metadata_value.get("DisplayName"), **kwargs
            )
            if object_name is not None:
                messages.append(create_expand_test_message(node, {object_name}, False))

                children = metadata_value.get("Children")

                if children is not None:
                    oid = kwargs[key + "_OID"]
                    next_node = node + f"{oid}/"
                    messages.append(
                        create_expand_test_message(next_node, set(children.keys()), False)
                    )
                    self.create_expand_messages(
                        children,
                        next_node + "{0}/",
                        create_expand_test_message,
                        messages,
                        **kwargs,
                    )

    def execute_script(self, script: str, connection: "psycopg.Connection"):
        cursor = connection.cursor()
        cursor.execute(script)
        return cursor

    def get_object_name(self, key: str, display_template: str, **kwargs):
        name = kwargs.get(key + "_Name")

        if name is not None and display_template is not None:
            return display_template.format(name)

        return name

    def delete_role(self, connection: "psycopg.Connection", role_name):
        cursor = connection.cursor()
        drop_role_script = 'DROP ROLE "' + role_name + '"'
        cursor.execute(drop_role_script)
        return cursor
