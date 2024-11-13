# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for generating JSON Schema and TypeScript interfaces"""

import json
import subprocess
from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.utils.serialization import convert_to_dict
from ossdbtoolsservice.utils.markdown import create_example_instance
from ossdbtoolsservice.connection.contracts import ConnectionDetails, ConnectRequestParams

from ossdbtoolsservice.admin import AdminService
from ossdbtoolsservice.capabilities.capabilities_service import CapabilitiesService
from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.disaster_recovery.disaster_recovery_service import DisasterRecoveryService
from ossdbtoolsservice.hosting import JSONRPCServer, ServiceProvider
from ossdbtoolsservice.language import LanguageService
from ossdbtoolsservice.metadata import MetadataService
from ossdbtoolsservice.object_explorer import ObjectExplorerService
from ossdbtoolsservice.query_execution import QueryExecutionService
from ossdbtoolsservice.scripting.scripting_service import ScriptingService
from ossdbtoolsservice.edit_data.edit_data_service import EditDataService
from ossdbtoolsservice.tasks import TaskService
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.workspace import WorkspaceService

def generate_json_schema_from_object(obj):
    """Generate JSON Schema from an instance of an object."""
    schema = {
        "title": obj.__class__.__name__,
        "type": "object",
        "properties": {},
        "required": []
    }
    obj_dict = convert_to_dict(obj)
    for key, value in obj_dict.items():
        schema["properties"][key] = {"type": type(value).__name__}
        schema["required"].append(key)
    return schema

def generate_typescript_interfaces_from_schema(schema: dict, output_file: str):
    """Generate TypeScript interfaces from JSON Schema using datamodel-code-generator."""
    schema_json = json.dumps(schema, indent=4)
    with open('schema.json', 'w') as f:
        f.write(schema_json)
    
    subprocess.run([
        'datamodel-code-generator',
        '--input', 'schema.json',
        '--input-file-type', 'jsonschema',
        '--output', output_file
    ])

if __name__ == '__main__':
    # Create the service provider and add the providers to it
    services = {
        constants.ADMIN_SERVICE_NAME: AdminService,
        constants.CAPABILITIES_SERVICE_NAME: CapabilitiesService,
        constants.CONNECTION_SERVICE_NAME: ConnectionService,
        constants.DISASTER_RECOVERY_SERVICE_NAME: DisasterRecoveryService,
        constants.LANGUAGE_SERVICE_NAME: LanguageService,
        constants.METADATA_SERVICE_NAME: MetadataService,
        constants.OBJECT_EXPLORER_NAME: ObjectExplorerService,
        constants.QUERY_EXECUTION_SERVICE_NAME: QueryExecutionService,
        constants.SCRIPTING_SERVICE_NAME: ScriptingService,
        constants.WORKSPACE_SERVICE_NAME: WorkspaceService,
        constants.EDIT_DATA_SERVICE_NAME: EditDataService,
        constants.TASK_SERVICE_NAME: TaskService
    }

    for messageConfig in IncomingMessageConfiguration.message_configurations:
        print(f"Message: {messageConfig.method} - {messageConfig.parameter_class}")
        example_instance = create_example_instance(messageConfig.parameter_class)
        schema = generate_json_schema_from_object(example_instance)
        print(json.dumps(schema, indent=4))

    # Generate TypeScript interfaces from the schema
    generate_typescript_interfaces_from_schema(schema, 'model.ts')