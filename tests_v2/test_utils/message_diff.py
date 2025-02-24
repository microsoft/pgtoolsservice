"""Utilities around comparing RPC messages"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from ossdbtoolsservice.hosting.lsp_message import (
    LSPNotificationMessage,
    LSPRequestMessage,
    LSPResponseErrorMessage,
    LSPResponseResultMessage,
)

T = TypeVar(
    "T",
    bound=LSPRequestMessage
    | LSPResponseErrorMessage
    | LSPResponseResultMessage
    | LSPNotificationMessage,
)


@dataclass
class DictDiffResult:
    diff: dict[str, tuple[Any, Any]]
    replace_map: dict[str, list[tuple[Any, Any]]]


def dict_diff(
    expected: dict[str, Any],
    actual: dict[str, Any],
    ignore_properties: list[str | Callable[[Any], bool]] | None = None,
    replace_map: dict[str, list[tuple[Any, Any]]] | None = None,
    match_properties: dict[str, Callable[[Any, Any], bool]] | None = None,
) -> DictDiffResult:
    """
    Do a deep comparison of two dictionaries and return a DictDiffResult containing:
      - diff: A dictionary of differences keyed by dot-delimited property paths,
        with each value as a tuple (expected, actual).
      - replace_map: A new copy of the provided mapping updated with any
        replacements detected (see below).
      - match_properties: A mapping of properties to functions that return
        True if the values match, False otherwise.

    For any property in ignore_properties, the value is not checked.
    For any property in replace_map, if the values differ, a tuple (expected, actual)
    is appended to the list for that property. No further deep-check is
    performed on these keys.

    Args:
        expected: The expected dictionary.
        actual: The actual dictionary.
        ignore_properties: A list of properties to ignore during comparison.
            Can be a property name or a callable that returns a bool.
        replace_map: A mapping of properties to replacement tuples.
        match_properties: A mapping of properties to functions that return
            True if the values match, False otherwise.
    Returns:
        A DictDiffResult containing the differences and updated replace_map.
    """
    if ignore_properties is None:
        ignore_properties = []

    # Create a new copy of replace_properties if provided; otherwise use an empty dict.
    new_replace_properties: dict[str, list[tuple[Any, Any]]] = (
        {k: list(v) for k, v in replace_map.items()} if replace_map is not None else {}
    )

    differences: dict[str, tuple[Any, Any]] = {}

    def compare(path: str, exp_val: Any, act_val: Any) -> None:
        # If this property is to be ignored, do nothing.
        if _property_match(path, act_val, ignore_properties) is not None:
            return

        # If this property is flagged for replacement, record the mapping (if different)
        # and don't add the difference.
        if path in new_replace_properties:
            if exp_val != act_val:
                new_replace_properties[path].append((exp_val, act_val))
            return

        # If this property has a custom match function, use it.
        if match_properties:
            match_func_key = _property_match(path, act_val, match_properties)
            if match_func_key is not None:
                if not match_properties[match_func_key](exp_val, act_val):
                    differences[path] = (exp_val, act_val)
                return

        # If both values are dictionaries, compare keys recursively.
        if isinstance(exp_val, dict) and isinstance(act_val, dict):
            keys = set(exp_val.keys()) | set(act_val.keys())
            for key in keys:
                new_path = f"{path}.{key}" if path else key
                if key not in exp_val:
                    differences[new_path] = (None, act_val[key])
                elif key not in act_val:
                    differences[new_path] = (exp_val[key], None)
                else:
                    compare(new_path, exp_val[key], act_val[key])
            return

        # If both values are lists, compare element by element.
        if isinstance(exp_val, list) and isinstance(act_val, list):
            if len(exp_val) != len(act_val):
                differences[path] = (exp_val, act_val)
            else:
                for i, (sub_exp, sub_act) in enumerate(zip(exp_val, act_val)):
                    new_path = f"{path}.{i}" if path else str(i)
                    compare(new_path, sub_exp, sub_act)
            return

        # For all other types, if they differ, record the difference.
        if exp_val != act_val:
            differences[path] = (exp_val, act_val)

    # Compare top-level keys.
    all_keys = set(expected.keys()) | set(actual.keys())
    for key in all_keys:
        current_path = key
        if key not in expected:
            differences[current_path] = (None, actual[key])
        elif key not in actual:
            differences[current_path] = (expected[key], None)
        else:
            compare(current_path, expected[key], actual[key])

    return DictDiffResult(diff=differences, replace_map=new_replace_properties)


def replace_properties(
    d: dict[str, Any],
    replace_map: dict[str, list[tuple[Any, Any]]],
) -> dict[str, Any]:
    """Replaces values of properties according to the replace map.

    If any property in the replace_map is encountered while recursing the dictionary,
    and it contains a value that matches the first element of a tuple in the list,
    the value is replaced with the second element of the tuple.

    The keys of the replace_map are dot-delimited paths to properties in the dictionary.

    Args:
        d: The dictionary to modify.
        replace_map: The mapping of properties to replacement tuples.
    Returns:
        The modified dictionary.
    """

    def _replace(val: Any, current_path: str) -> Any:
        # If the current property path is flagged for replacement, check for a match.
        if current_path in replace_map:
            for expected_val, replacement_val in replace_map[current_path]:
                if val == expected_val:
                    return replacement_val
            # If none of the expected values match, return the value as-is
            return val

        # Recurse into dictionaries.
        if isinstance(val, dict):
            new_dict = {}
            for key, sub_val in val.items():
                new_path = key if current_path == "" else f"{current_path}.{key}"
                new_dict[key] = _replace(sub_val, new_path)
            return new_dict
        # Recurse into lists.
        elif isinstance(val, list):
            new_list = []
            for i, item in enumerate(val):
                new_path = str(i) if current_path == "" else f"{current_path}.{i}"
                new_list.append(_replace(item, new_path))
            return new_list
        else:
            return val

    return _replace(d, "")


def diff_messages(
    expected: T,
    actual: T,
    ignore_properties: list[str | Callable[[Any], bool]] | None = None,
    replace_map: dict[str, list[tuple[Any, Any]]] | None = None,
    match_properties: dict[str, Callable[[Any, Any], bool]] | None = None,
) -> DictDiffResult:
    """Compare two messages and return a DictDiffResult containing the differences.

    Args:
        expected: The expected message.
        actual: The actual message.
        ignore_properties: A list of properties to ignore during comparison. This
            can be a property name or a callable that returns a bool.
        replace_map: A mapping of properties to replacement tuples.
        match_properties: A mapping of properties to functions that return
            True if the values match, False otherwise.
    Returns:
        A DictDiffResult containing the differences and updated replace_map.
    """
    result = dict_diff(
        expected.model_dump(by_alias=True),
        actual.model_dump(by_alias=True),
        ignore_properties=ignore_properties,
        replace_map=replace_map,
        match_properties=match_properties,
    )
    return result


def _property_match(
    path: str, value: Any, conditions: Iterable[str | Callable[[Any], bool]]
) -> str | None:
    """Check if a property path matches any of the given conditions.

    Checks if the path is in the given sequence of properties or matches
    any of the callables.
    property in the path is in in a wildcard property, e.g. '*.property'.

    Args:
        path: The property path to check.
        value: The value of the property.
        conditions: The list of conditions to check against.
            Can be a property name or a callable that returns a bool.


    Returns:
        The matching property, or None if no match is found.
    """
    for match_value in conditions:
        if callable(match_value):
            if match_value(value):
                return path
        else:
            if path == match_value:
                return match_value
            if match_value.startswith("*.") and path.endswith(match_value[1:]):
                return match_value

    return None
