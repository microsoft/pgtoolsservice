# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for generating JSON Schema and TypeScript interfaces"""

import enum
import inspect
import json
import os
from typing import Any, Dict, Optional, Type, Union

from ossdbtoolsservice.admin import AdminService
from ossdbtoolsservice.capabilities.capabilities_service import CapabilitiesService
from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.disaster_recovery.disaster_recovery_service import (
    DisasterRecoveryService,
)
from ossdbtoolsservice.edit_data.edit_data_service import EditDataService
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.language import LanguageService
from ossdbtoolsservice.metadata import MetadataService
from ossdbtoolsservice.object_explorer import ObjectExplorerService
from ossdbtoolsservice.query_execution import QueryExecutionService
from ossdbtoolsservice.scripting.scripting_service import ScriptingService
from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.tasks import TaskService
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.workspace import WorkspaceService

# Registry to store reusable schemas
schema_registry: Dict[str, Dict[str, Any]] = {}


def class_to_json_schema(cls: Type) -> Dict[str, Any]:
    # Check if the schema for this class already exists in the registry
    if cls.__name__ in schema_registry:
        return schema_registry[cls.__name__]

    # Ensure all base classes are processed first
    base_schemas = []
    for base in cls.__bases__:
        if base in [object, Serializable]:  # Skip `object` and `Serializable` as a base class
            continue
        elif base.__name__ not in schema_registry:
            # Process base class first if it hasn’t been processed
            class_to_json_schema(base)
        base_schemas.append({"$ref": f"#/definitions/{base.__name__}"})

    # Define the initial schema structure
    schema = {"title": cls.__name__, "type": "object", "properties": {}, "required": []}

    # If the class has base classes, use allOf to include them
    if base_schemas:
        schema["allOf"] = base_schemas

    # Register the schema structure in the registry before fully populating it
    schema_registry[cls.__name__] = schema

    # Get all type hints, including those defined directly as class variables
    hints = cls.__annotations__

    # Include properties defined with `@property` decorators
    for name, method in inspect.getmembers(cls, lambda o: isinstance(o, property)):
        # Add property to schema with appropriate type (string for str, integer for int, etc.)
        prop_type = hints.get(name, str)  # Default to `str` if type hint is missing
        schema["properties"][name] = get_schema_type(prop_type)

        # Properties without a setter are read-only
        if method.fset is None:
            schema["properties"][name]["readOnly"] = True

        # If the property is required (doesn't default to None), add it to `required`
        if name in hints and not is_optional_type(hints[name]):
            schema["required"].append(name)

    # Include other non-property attributes from type hints
    for attr, attr_type in hints.items():
        if attr not in schema["properties"]:  # Avoid duplicate entries for properties
            schema["properties"][attr] = get_schema_type(attr_type)
            if not is_optional_type(attr_type):
                schema["required"].append(attr)

    return schema


def enum_to_json_schema(enum_class: Type[enum.Enum]) -> Dict[str, Any]:
    """Convert an Enum class to a JSON schema enum definition."""
    # Define the schema structure
    schema = {
        "title": enum_class.__name__,
        "type": "string",
        "enum": [item.value for item in enum_class],
        "description": enum_class.__doc__ or "",
    }

    # Register the schema structure in the registry before fully populating it
    schema_registry[enum_class.__name__] = schema
    return schema


def get_schema_type(attr_type: Type) -> Dict[str, Any]:
    """Convert Python types to JSON schema types and handle nested classes."""
    if attr_type == str:
        return {"type": "string"}
    elif attr_type == int:
        return {"type": "integer"}
    elif attr_type == bool:
        return {"type": "boolean"}
    elif attr_type == float:
        return {"type": "number"}
    elif attr_type == list:
        return {"type": "array"}
    elif attr_type in [dict, object]:
        return {"type": "object"}
    elif inspect.isclass(attr_type):
        # Ensure the schema for the nested class is created and registered
        if attr_type.__name__ not in schema_registry:
            if issubclass(attr_type, enum.Enum):
                enum_to_json_schema(attr_type)
            else:
                class_to_json_schema(attr_type)
        # Use reference if the schema is already in the registry
        return {"$ref": f"#/definitions/{attr_type.__name__}"}
    elif hasattr(attr_type, "__origin__") and attr_type.__origin__ is Union:
        # Handle Optional or Union types
        inner_types = [t for t in attr_type.__args__ if t is not type(None)]
        if len(inner_types) == 1:
            return get_schema_type(inner_types[0])
        return {"anyOf": [get_schema_type(t) for t in inner_types]}
    return {"type": "string"}  # Default to string for unknown types


def is_optional_type(attr_type: Type) -> bool:
    """Check if the type is Optional."""
    return Union[None, attr_type] == Optional[attr_type] or (
        hasattr(attr_type, "__origin__")
        and attr_type.__origin__ is Union
        and type(None) in attr_type.__args__
    )


def generate_full_schema() -> Dict[str, Any]:
    """Generate a unified JSON schema containing multiple classes."""
    unified_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "UnifiedSchema",
        "type": "object",
        "definitions": {},
        "properties": {},
    }

    for name, schema in schema_registry.items():
        unified_schema["definitions"][name] = schema
        unified_schema["properties"][name] = {"$ref": f"#/definitions/{name}"}

    return unified_schema


def save_json_schema_to_file(schema: dict, file_path: str):
    """Save JSON Schema to a file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(schema, f, indent=4)


if __name__ == "__main__":
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
        constants.TASK_SERVICE_NAME: TaskService,
    }

    # Convert all parameter classes registered in IncomingMessageConfiguration to JSON schema
    for messageConfig in IncomingMessageConfiguration.message_configurations:
        print(f"Message: {messageConfig.method} - {messageConfig.parameter_class}")
        class_to_json_schema(messageConfig.parameter_class)

    # Convert all outgoing message classes registered in OutgoingMessageRegistration to JSON schema
    for outgoingMessage in OutgoingMessageRegistration.message_configurations:
        print(f"Message: {outgoingMessage}")
        class_to_json_schema(outgoingMessage)

    # Generate the full schema and save it to a JSON schema file
    full_schema = generate_full_schema()
    schema_file_path = "build/dto_generator/full_schema.json"
    save_json_schema_to_file(full_schema, schema_file_path)
