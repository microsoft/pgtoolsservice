"""Tests for the testing utilities."""

from typing import Any, Callable

from .message_diff import dict_diff, replace_properties

# dict_diff


def test_identical_dicts() -> None:
    expected = {"a": 1, "b": {"c": 2}}
    actual = {"a": 1, "b": {"c": 2}}
    result = dict_diff(expected, actual)
    assert result.diff == {}
    # When no replace_properties are provided, it returns an empty dict.
    assert result.replace_map == {}


def test_top_level_difference() -> None:
    expected = {"a": 1, "b": 2}
    actual = {"a": 2, "b": 2}
    result = dict_diff(expected, actual)
    assert result.diff == {"a": (1, 2)}
    assert result.replace_map == {}


def test_missing_key_in_actual() -> None:
    expected = {"a": 1, "b": 2}
    actual = {"a": 1}
    result = dict_diff(expected, actual)
    assert result.diff == {"b": (2, None)}
    assert result.replace_map == {}


def test_missing_key_in_expected() -> None:
    expected = {"a": 1}
    actual = {"a": 1, "b": 2}
    result = dict_diff(expected, actual)
    assert result.diff == {"b": (None, 2)}
    assert result.replace_map == {}


def test_nested_dictionary_difference() -> None:
    expected = {"a": {"b": 1, "c": 2}}
    actual = {"a": {"b": 1, "c": 3}}
    result = dict_diff(expected, actual)
    # Only the nested property "a.c" differs.
    assert result.diff == {"a.c": (2, 3)}
    assert result.replace_map == {}


def test_list_element_difference() -> None:
    expected = {"a": [1, 2, 3]}
    actual = {"a": [1, 4, 3]}
    result = dict_diff(expected, actual)
    # List element at index 1 differs.
    assert result.diff == {"a.1": (2, 4)}
    assert result.replace_map == {}


def test_list_length_difference() -> None:
    expected = {"a": [1, 2, 3]}
    actual = {"a": [1, 2]}
    result = dict_diff(expected, actual)
    # When list lengths differ, the whole list is recorded.
    assert result.diff == {"a": ([1, 2, 3], [1, 2])}
    assert result.replace_map == {}


def test_nested_list_in_dictionary() -> None:
    expected = {"a": {"b": [1, {"c": 2}]}}
    actual = {"a": {"b": [1, {"c": 3}]}}
    result = dict_diff(expected, actual)
    # The difference is deep inside the list (property path "a.b.1.c").
    assert result.diff == {"a.b.1.c": (2, 3)}
    assert result.replace_map == {}


def test_ignore_properties() -> None:
    expected = {"a": {"b": 1, "c": 2}}
    actual = {"a": {"b": 2, "c": 2}}
    ignore_props: list[str | Callable[[Any], bool]] = ["a.b"]
    result = dict_diff(expected, actual, ignore_properties=ignore_props)
    # The difference at "a.b" is ignored so no difference should be reported.
    assert result.diff == {}
    assert result.replace_map == {}


def test_ignore_nested_properties() -> None:
    expected = {"a": {"b": 1, "c": {"d": 2, "e": 3}}}
    actual = {"a": {"b": 2, "c": {"d": 2, "e": 4}}}
    ignore_props: list[str | Callable[[Any], bool]] = ["a.b", "a.c.e"]
    result = dict_diff(expected, actual, ignore_properties=ignore_props)
    # Both "a.b" and "a.c.e" are ignored so no diff should be recorded.
    assert result.diff == {}
    assert result.replace_map == {}


def test_replace_properties() -> None:
    expected = {"a": {"b": 1}}
    actual = {"a": {"b": 2}}
    # Provide a list for the property "a.b" so that it gets updated.
    replace_props: dict[str, list[tuple[Any, Any]]] = {"a.b": []}
    result = dict_diff(expected, actual, replace_map=replace_props)
    # The diff should not contain the difference
    assert result.diff == {}
    # The new replace_properties copy should reflect the update.
    assert result.replace_map["a.b"] == [(1, 2)]
    # Also verify that the original replace_props was not mutated.
    assert replace_props["a.b"] == []


# replace_properties


def test_replace_nested_properties() -> None:
    expected = {"a": {"b": 1, "c": 2}}
    actual = {"a": {"b": 1, "c": 3}}
    replace_props: dict[str, list[tuple[Any, Any]]] = {"a.c": []}
    result = dict_diff(expected, actual, replace_map=replace_props)
    assert result.diff == {}
    assert result.replace_map["a.c"] == [(2, 3)]
    # Original dict remains unchanged.
    assert replace_props["a.c"] == []


def test_replace_top_level() -> None:
    d = {"a": 1, "b": 2}
    replace_map = {"a": [(1, 10)]}
    result = replace_properties(d, replace_map)
    assert result == {"a": 10, "b": 2}


def test_replace_nested() -> None:
    d = {"a": {"b": 1}}
    replace_map = {"a.b": [(1, 10)]}
    result = replace_properties(d, replace_map)
    assert result == {"a": {"b": 10}}


def test_replace_in_list() -> None:
    d = {"a": [1, 2, 3]}
    replace_map = {"a.1": [(2, 20)]}
    result = replace_properties(d, replace_map)
    assert result == {"a": [1, 20, 3]}


def test_no_replacement_when_no_match() -> None:
    d = {"a": 1}
    replace_map = {"a": [(2, 20)]}
    result = replace_properties(d, replace_map)
    assert result == {"a": 1}


def test_multiple_replacements() -> None:
    d = {"a": 1}
    # Multiple tuples: only the first matching tuple should be applied.
    replace_map = {"a": [(2, 20), (1, 10)]}
    result = replace_properties(d, replace_map)
    assert result == {"a": 10}


def test_replace_container_flag() -> None:
    # If the container itself is flagged, no recursion is done.
    d = {"a": {"b": 1}}
    replace_map = {"a": [({"b": 1}, {"b": 10})]}
    result = replace_properties(d, replace_map)
    assert result == {"a": {"b": 10}}


def test_replace_list_of_dicts() -> None:
    d = {"a": [{"b": 1}, {"b": 2}]}
    replace_map = {"a.0.b": [(1, 10)], "a.1.b": [(2, 20)]}
    result = replace_properties(d, replace_map)
    assert result == {"a": [{"b": 10}, {"b": 20}]}


def test_flagged_no_replacement() -> None:
    # When the property is flagged but the value doesn't match any expected value,
    # the value remains unchanged.
    d = {"a": {"b": 1, "c": 2}}
    replace_map = {"a.b": [(2, 20)]}  # a.b is 1 so no replacement.
    result = replace_properties(d, replace_map)
    assert result == {"a": {"b": 1, "c": 2}}


def test_no_flag_no_change() -> None:
    # When the replace_map is empty, the original dictionary is returned unchanged.
    d = {"a": {"b": 1, "c": 2}}
    replace_map: dict[str, list[tuple[Any, Any]]] = {}
    result = replace_properties(d, replace_map)
    assert result == {"a": {"b": 1, "c": 2}}
