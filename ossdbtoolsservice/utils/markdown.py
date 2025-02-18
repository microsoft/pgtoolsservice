# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for generating Markdown documentation"""

import json
import random
import string
from enum import Enum
from typing import Any

from ossdbtoolsservice.utils.serialization import convert_to_dict


def generate_requests_markdown(server, logger, output_file="docs/Requests.md"):
    # Dictionary to store requests grouped by service
    services_dict = {}

    # Loop over request handlers create a sample request for each and serialize it to JSON
    for method, req_handler in server._request_handlers.items():
        try:
            example_instance = None
            if req_handler.class_:
                example_instance = create_example_instance(req_handler.class_)

            # Construct the JSON-RPC request structure
            json_rpc_request = {
                "jsonrpc": "2.0",
                "method": method,
                "id": random.randint(1, 1000000),
                "params": example_instance,
            }

            # Convert the JSON-RPC request to a JSON string
            json_rpc_request_str = json.dumps(convert_to_dict(json_rpc_request), indent=4)
            logger.info(
                f"JSON-RPC request for {req_handler.class_} in "
                f"'{method}':\n {json_rpc_request_str}"
            )

            # Extract the service name from the method
            service_name = "base"
            service_name_split = method.split("/")
            if len(service_name_split) > 1:
                service_name = service_name_split[0]

            # Create an anchor link for the index
            anchor_link = method.replace("/", "").lower()

            # Initialize the service entry if it doesn't exist
            if service_name not in services_dict:
                services_dict[service_name] = {"index": [], "requests": []}

            # Append the request details to the service entry
            services_dict[service_name]["index"].append(f"- [{method}](#{anchor_link})")
            services_dict[service_name]["requests"].append(
                f"## {method}\n- **Class**: "
                f"{req_handler.class_.__name__ if req_handler.class_ else 'None'}\n"
                f"- **Method**: {method}\n- **Request JSON**:\n"
                f"```json\n{json_rpc_request_str}\n```"
            )  # noqa
        except TypeError as e:
            logger.error(
                f"Could not create example instance for {req_handler.class_} "
                f"in '{method}': {e}"
            )

    # Generate the Markdown content
    index_content = "# Index\n\n"
    requests_content = ""

    for service_name, service_data in services_dict.items():
        index_content += f"## {service_name}\n" + "\n".join(service_data["index"]) + "\n\n"
        requests_content += (
            f"# {service_name}\n\n" + "\n\n".join(service_data["requests"]) + "\n\n"
        )

    markdown_content = f"{index_content}\n\n# Requests\n\n{requests_content}"

    # Output the Markdown content to a file
    with open(output_file, "w") as f:
        f.write(markdown_content)


def generate_mock_data_for_type(field_type: type) -> Any:
    """Generate example mock data based on attribute type."""
    if field_type is int:
        return random.randint(1, 100)
    elif field_type is float:
        return round(random.uniform(1, 100), 2)
    elif field_type is str:
        return "".join(random.choices(string.ascii_letters, k=8))
    elif field_type is bool:
        return random.choice([True, False])
    elif field_type is list:
        return [generate_mock_data_for_type(int)]  # Example list with integers
    elif field_type is dict:
        return {"key": generate_mock_data_for_type(str)}  # Example dictionary
    elif isinstance(field_type, type) and issubclass(field_type, Enum):
        return list(field_type)[0]  # Return the first value of the enum
    return None  # Default for unhandled types


def create_example_instance(cls: type) -> Any:
    """Generate an example instance of a class with mock data."""
    if hasattr(cls, "__init__"):
        # Prepare constructor arguments with mock values
        init_args = {}
        init_signature = cls.__init__.__annotations__

        # Populate constructor arguments based on type hints
        for arg_name, arg_type in init_signature.items():
            if arg_name != "return":  # Skip the return annotation
                init_args[arg_name] = generate_mock_data_for_type(arg_type)

        # Create an instance with mock arguments, with special handling for enums.
        if isinstance(cls, type) and issubclass(cls, Enum):
            instance = list(cls)[0]  # Return the first value of the enum
        else:
            instance = cls(**init_args)

        # Handle any custom attributes
        if hasattr(cls, "get_child_serializable_types"):
            child_types = cls.get_child_serializable_types()
            for attr, child_cls in child_types.items():
                setattr(instance, attr, create_example_instance(child_cls))

        return instance

    raise TypeError(f"{cls} is not a serializable class")
