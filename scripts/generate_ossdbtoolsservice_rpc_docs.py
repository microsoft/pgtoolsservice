#!/usr/bin/env python3

import ast
import inspect
import io
import logging
import os
import sys

# Add the parent directory to the system path, which contains the ossdbtoolsservice package
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
sys.path.insert(0, parent_dir)

from ossdbtoolsservice.ossdbtoolsservice_main import _create_server


def introspect_class_props(cls):
    """Check for actual properties in the class, and their types"""
    class_properties = [
        name for name, value in inspect.getmembers(cls) if isinstance(value, property)
    ]
    annotations = getattr(cls, "__annotations__", {})
    return class_properties, annotations


def introspect_init_attributes_with_bases(cls):
    """Check for attributes defined in the __init__ method of the class and its base classes"""
    # Store attribute names and annotations
    attributes = {}

    # Some classes have properties defined other than in _init_
    class_props, class_annotations = introspect_class_props(cls)

    for prop in class_props:
        annotation = class_annotations.get(prop, None)
        attributes[prop] = annotation

    # Iterate over the class and its base classes in Method Resolution Order (MRO)
    for base in cls.__mro__:
        # Skip the 'object' class
        if base is object:
            continue

        # Get the source code of the base class
        try:
            source = inspect.getsource(base)
        except OSError:
            continue

        # Parse the source code into an AST
        tree = ast.parse(source)

        # Find the __init__ method in the class body
        init_function = None
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == base.__name__:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        init_function = item
                        break
                break

        if not init_function:
            # No __init__ method found in this class
            continue

        # Iterate over all nodes in the __init__ method
        for node in ast.walk(init_function):
            # Check for annotated assignments (e.g., self.x: int = 0)
            if isinstance(node, ast.AnnAssign):
                target = node.target
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    attr_name = target.attr
                    # Extract the annotation
                    try:
                        annotation = ast.unparse(node.annotation)
                    except AttributeError:
                        # For Python versions < 3.9
                        annotation = ast.get_source_segment(source, node.annotation)
                    attributes[attr_name] = annotation
            # Check for regular assignments (e.g., self.x = 0)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        attr_name = target.attr
                        # No annotation available in ast.Assign
                        attributes[attr_name] = None

    # Display results
    print(f"#### {cls.__name__}")
    if attributes:
        for attr_name, annotation in attributes.items():
            if annotation:
                print(f"- {attr_name}: `{annotation}`")
            else:
                print(f"- {attr_name}: `any`")


def print_docs():
    # Create an RPC server with the request handlers added
    logger = logging.getLogger("ossdbtoolsservice")
    stdin = io.open(sys.stdin.fileno(), "rb", buffering=0, closefd=False)
    std_out_wrapped = io.open(sys.stdout.fileno(), "wb", buffering=0, closefd=False)

    server = _create_server(stdin, std_out_wrapped, logger, "PGSQL")

    print("## Registered RPC methods", "\n")
    for method, handler in server._request_handlers.items():
        print(f"### {method}")
        try:
            introspect_init_attributes_with_bases(handler.class_)
        except Exception as e:
            print("- None")
        print("---", "\n")


if __name__ == "__main__":
    # if "--help" passed in, then print out usage()
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(
            "Prints out RPC methods that are currently registered in the ossdbtoolsservice",
            "RPC service and their input parameters. This script outputs markdown formatted",
            "text.",
        )
        sys.exit(0)

    print_docs()
