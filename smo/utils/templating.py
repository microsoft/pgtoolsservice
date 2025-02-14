# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
from typing import Dict, List, Optional, Tuple

import psycopg
from jinja2 import Environment, FileSystemLoader, Template

from .keywords import scan_keyword

TEMPLATE_ENVIRONMENTS: Dict[int, Environment] = {}
TEMPLATE_FOLDER_REGEX = re.compile(r"(\d+)\.(\d+)(?:_(\w+))?$")
TEMPLATE_SKIPPED_FOLDERS: List[str] = ["macros"]


def get_template_root(file_path: str, template_directory: str) -> str:
    return os.path.join(os.path.dirname(os.path.realpath(file_path)), template_directory)


def get_template_path(
    template_root: str, template_name: str, server_version: Tuple[int, int, int]
) -> str:
    """
    Checks for the existence of a template in a server specific version folder first,
    :param template_root: Root folder for the templates
    :param template_name: Filename of the template to look up
    :param server_version: Tuple of the connected server version components (major, minor, ignored)
    :return: Path to the desired template
    """
    # Step 1) Get the list of folders in the template folder that contains the
    # Step 1.1) Get the list of folders in the template root folder
    all_folders: List[str] = [os.path.normpath(x[0]) for x in os.walk(template_root)]

    # Step 1.2) Filter out the folders that don't contain the target template
    containing_folders: List[str] = [
        x for x in all_folders if template_name in next(os.walk(x))[2]
    ]

    def sortlist(item):
        number = os.path.basename(item).partition("_")[0]
        try:
            number = float(number)
        except ValueError:
            return 0
        return number

    containing_folders = sorted(containing_folders, key=sortlist)

    # Step 1.3) Reverse the order of the list, to allow processing from greatest version to lowest
    containing_folders = containing_folders[::-1]

    # Step 2) Iterate over the list of directories and check if the server version fits the bill
    for folder in containing_folders:
        # Skip over non-included folders
        if os.path.basename(folder) in TEMPLATE_SKIPPED_FOLDERS:
            continue

        # If we are at the default, we are at the end of the list, so it is the only valid match
        if folder.endswith(os.sep + "+default"):
            return os.path.join(folder, template_name)

        # Process the folder name with the regex
        match = TEMPLATE_FOLDER_REGEX.search(folder)
        if not match:
            # This indicates a serious bug that shouldn't occur in production code, so this needn't be localized.
            raise ValueError(
                f"Templates folder {template_root} contains improperly formatted folder name {folder}"
            )
        captures = match.groups()
        major = int(captures[0])
        minor = int(captures[1])
        modifier = captures[2]

        if modifier is None:
            # Version number must match exactly
            if major == int(server_version[0]) and minor == server_version[1]:
                return os.path.join(folder, template_name)
        elif modifier == "plus":
            # Version can be equal to or greater than
            if server_version[0] > major or (
                server_version[0] == major and server_version[1] >= minor
            ):
                return os.path.join(folder, template_name)
        # TODO: Modifier is minus

    # If we make it to here, the template doesn't exist.
    # This indicates a serious bug that shouldn't occur in production code, so this doesn't need to be localized.
    raise ValueError(f"Template folder {template_root} does not contain {template_name}")


def render_template(
    template_path: str, macro_roots: Optional[List[str]] = None, **context
) -> str:
    """
    Renders a template from the template folder with the given context.
    :param template_path: the path to the template to be rendered
    :param macro_roots: optional root folders to add for macros
    :param context: the variables that should be available in the context of the template.
    :return: The template rendered with the provided context
    """
    # Determine the order of the paths to check
    # 1) Look in the directory of the template path FIRST
    # 2) Look in any macro folders SECOND
    # 3) TODO: If necessary, add a global macro directory to check LAST
    path, filename = os.path.split(template_path)
    macro_roots = macro_roots if macro_roots is not None else []
    paths = [path, *macro_roots]
    environment_key = _hash_source_list(paths)

    if environment_key not in TEMPLATE_ENVIRONMENTS:
        # Create the filesystem loader that will look in template folder FIRST
        loader: FileSystemLoader = FileSystemLoader(paths)

        # Create the environment and add the basic filters
        new_env: Environment = Environment(loader=loader, trim_blocks=True)
        new_env.filters["qtIdent"] = qt_ident
        new_env.filters["qtTypeIdent"] = qt_type_ident
        new_env.filters["hasAny"] = has_any
        new_env.filters["string_convert"] = string_convert
        new_env.filters["qtLiteral"] = qt_literal

        TEMPLATE_ENVIRONMENTS[environment_key] = new_env

    env = TEMPLATE_ENVIRONMENTS[environment_key]
    to_render = env.get_template(filename)
    return to_render.render(**context)


def render_template_string(source, **context):
    """
    Renders a template from the given template source string with the given context. Template variables will be
    autoescaped.
    :param source: the source code of the template to be rendered
    :param context: the variables that should be available in the context of the template.
    :return: The template rendered with the provided context
    """
    template = Template(source)
    return template.render(context)


def string_convert(value):
    """
    Quotes variables embedded within templates
    :param - value to be quoted

    E.g:
        6 -> '6'
        "sql" -> "'sql'"
    """
    return "'{}'".format(str(value))


def _hash_source_list(sources: list) -> int:
    return hash(frozenset(sources))


##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2017, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################


def qt_type_ident(conn, *args):
    # We're not using the conn object at the moment, but - we will
    # modify the
    # logic to use the server version specific keywords later.
    res = None
    value = None

    for val in args:
        # DataType doesn't have len function then convert it to string
        if not hasattr(val, "__len__"):
            val = str(val)

        if len(val) == 0:
            continue
        value = val

        if needs_quoting(val, True):
            value = value.replace('"', '""')
            value = '"' + value + '"'

        res = ((res and res + ".") or "") + value

    return res


def qt_ident(conn, *args):
    # We're not using the conn object at the moment, but - we will
    # modify the logic to use the server version specific keywords later.
    res = None
    value = None

    for val in args:
        if isinstance(val, list):
            return map(lambda w: qt_ident(conn, w), val)

        # DataType doesn't have len function then convert it to string
        if not hasattr(val, "__len__"):
            val = str(val)

        if len(val) == 0:
            continue

        value = val

        if needs_quoting(val, False):
            value = value.replace('"', '""')
            value = '"' + value + '"'

        res = ((res and res + ".") or "") + value

    return res


def qt_literal(value, conn, force_quote=False):
    res = value

    if conn:
        try:
            if type(conn) != psycopg.Connection and type(conn) != psycopg.AsyncConnection:
                conn = conn.conn
            res = psycopg.sql.Literal(value).as_string(conn).strip()
        except Exception:
            print("Exception", value)

    if force_quote is True:
        # Convert the input to the string to use the startsWith(...)
        res = str(res)
        if not res.startswith("'"):
            return "'" + res + "'"

    return res


def has_any(data, keys):
    """
    Checks any one of the keys present in the data given
    """
    if data is None and not isinstance(data, dict):
        return False

    if keys is None and not isinstance(keys, list):
        return False

    for key in keys:
        if key in data:
            return True

    return False


def needs_quoting(key, for_types):
    value = key
    val_noarray = value

    # check if the string is number or not
    if isinstance(value, int):
        return True
    # certain types should not be quoted even though it contains a space.
    # Evilness.
    elif for_types and value[-2:] == "[]":
        val_noarray = value[:-2]

    if for_types and val_noarray.lower() in [
        "bit varying",
        '"char"',
        "character varying",
        "double precision",
        "timestamp without time zone",
        "timestamp with time zone",
        "time without time zone",
        "time with time zone",
        '"trigger"',
        '"unknown"',
    ]:
        return False

    # If already quoted?, If yes then do not quote again
    if (
        for_types
        and val_noarray
        and (val_noarray.startswith('"') or val_noarray.endswith('"'))
    ):
        return False

    if "0" <= val_noarray[0] <= "9":
        return True

    if re.search("[^a-z_0-9]+", val_noarray):
        return True

    # check string is keywaord or not
    category = scan_keyword_extra_lookup(value)

    if category is None:
        return False

    # UNRESERVED_KEYWORD
    if category == 0:
        return False

    # COL_NAME_KEYWORD
    if for_types and category == 1:
        return False

    return True


def scan_keyword_extra_lookup(key):
    # UNRESERVED_KEYWORD      0
    # COL_NAME_KEYWORD        1
    # TYPE_FUNC_NAME_KEYWORD  2
    # RESERVED_KEYWORD        3

    return _EXTRA_KEYWORDS.get(key, None) or scan_keyword(key)


_EXTRA_KEYWORDS = {
    "connect": 3,
    "convert": 3,
    "distributed": 0,
    "exec": 3,
    "log": 0,
    "long": 3,
    "minus": 3,
    "nocache": 3,
    "number": 3,
    "package": 3,
    "pls_integer": 3,
    "raw": 3,
    "return": 3,
    "smalldatetime": 3,
    "smallfloat": 3,
    "smallmoney": 3,
    "sysdate": 3,
    "systimestap": 3,
    "tinyint": 3,
    "tinytext": 3,
    "varchar2": 3,
}
