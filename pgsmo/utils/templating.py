# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
from typing import Dict, List, Tuple

from jinja2 import Environment, FileSystemLoader, Template
from psycopg2.extensions import adapt

TEMPLATE_ENVIRONMENTS: Dict[str, Environment] = {}
TEMPLATE_FOLDER_REGEX = re.compile('(\d+)\.(\d+)(?:_(\w+))?$')
TEMPLATE_SKIPPED_FOLDERS: List[str] = ['macros']


def get_template_root(file_path: str, template_directory: str) -> str:
    return os.path.join(os.path.dirname(os.path.realpath(file_path)), template_directory)


def get_template_path(template_root: str, template_name: str, server_version: Tuple[int, int, int]) -> str:
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
    containing_folders: List[str] = [x for x in all_folders if template_name in next(os.walk(x))[2]]

    # Step 1.3) Reverse the order of the list, to allow processing from greatest version to lowest
    containing_folders = containing_folders[::-1]

    # Step 2) Iterate over the list of directories and check if the server version fits the bill
    for folder in containing_folders:
        # Skip over non-included folders
        if os.path.basename(folder) in TEMPLATE_SKIPPED_FOLDERS:
            continue

        # If we are at the default, we are at the end of the list, so it is the only valid match
        if folder.endswith(os.sep + '+default'):
            return os.path.join(folder, template_name)

        # Process the folder name with the regex
        match = TEMPLATE_FOLDER_REGEX.search(folder)
        if not match:
            # This indicates a serious bug that shouldn't occur in production code, so this needn't be localized.
            raise ValueError(f'Templates folder {template_root} contains improperly formatted folder name {folder}')
        captures = match.groups()
        major = int(captures[0])
        minor = int(captures[1])
        modifier = captures[2]

        if modifier is None:
            # Version number must match exactly
            if major == int(server_version[0]) and minor == server_version[1]:
                return os.path.join(folder, template_name)
        elif modifier == 'plus':
            # Version can be equal to or greater than
            if server_version[0] >= major and server_version[1] >= minor:
                return os.path.join(folder, template_name)
        # TODO: Modifier is minus

    # If we make it to here, the template doesn't exist.
    # This indicates a serious bug that shouldn't occur in production code, so this doesn't need to be localized.
    raise ValueError(f'Template folder {template_root} does not contain {template_name}')


def render_template(template_path: str, paths_to_add=None, filters_to_add=None, **context) -> str:
    """
    Renders a template from the template folder with the given context.
    :param template_path: the path to the template to be rendered
    :param context: the variables that should be available in the context of the template.
    :return: The template rendered with the provided context
    """
    path, filename = os.path.split(template_path)
    paths = [path]
    if (paths_to_add is not None):
        paths += paths_to_add

    for path in paths:
        if path not in TEMPLATE_ENVIRONMENTS:
            # Create the filesystem loader that will look in template folder FIRST
            template_root = os.path.dirname(os.path.dirname(template_path))
            if (template_root not in TEMPLATE_ENVIRONMENTS):
                paths.append(template_root)
            loader: FileSystemLoader = FileSystemLoader(paths)

            # Create the environment and add the basic filters
            new_env: Environment = Environment(loader=loader)
            new_env.filters['qtLiteral'] = qt_literal
            new_env.filters['qtIdent'] = qt_ident
            new_env.filters['qtTypeIdent'] = qt_type_ident

            TEMPLATE_ENVIRONMENTS[path] = new_env
            break

    if (filters_to_add is not None):
        for filter_name, function in filters_to_add.items():
            TEMPLATE_ENVIRONMENTS[path].filters[filter_name] = function

    env = TEMPLATE_ENVIRONMENTS[path]
    to_render = env.get_template(filename)
    return to_render.render(context)


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

##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2017, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################


def qt_literal(value):
    adapted = adapt(value)

    # Not all adapted objects have encoding
    # e.g.
    # psycopg2.extensions.BOOLEAN
    # psycopg2.extensions.FLOAT
    # psycopg2.extensions.INTEGER
    # etc...
    if hasattr(adapted, 'encoding'):
        adapted.encoding = 'utf8'
    res = adapted.getquoted()

    if isinstance(res, bytes):
        return res.decode('utf-8')
    return res


def qt_type_ident(conn, *args):
    # We're not using the conn object at the moment, but - we will modify the
    # logic to use the server version specific keywords later.
    res = None
    value = None

    for val in args:
        if len(val) == 0:
            continue
        value = val

        if needs_quoting(val, True):
            value = value.replace("\"", "\"\"")
            value = "\"" + value + "\""

        res = ((res and res + '.') or '') + value

    return res


def qt_ident(conn, *args):
    # We're not using the conn object at the moment, but - we will modify the
    # logic to use the server version specific keywords later.
    res = None
    value = None

    for val in args:
        if type(val) == list:
            return map(lambda w: qt_ident(conn, w), val)

        if len(val) == 0:
            continue

        value = val

        if needs_quoting(val, False):
            value = value.replace("\"", "\"\"")
            value = "\"" + value + "\""

        res = ((res and res + '.') or '') + value

    return res


def has_any(data, keys):
    """
    Checks any one of the keys present in the data given
    """
    if data is None and type(data) != dict:
        return False

    if keys is None and type(keys) != list:
        return False

    for key in keys:
        if key in data:
            return True

    return False


def needs_quoting(key, for_types):
    value = key
    val_no_array = value

    # check if the string is number or not
    if isinstance(value, int):
        return True
    # certain types should not be quoted even though it contains a space. Evilness.
    elif for_types and value[-2:] == u"[]":
        val_no_array = value[:-2]

    if for_types and val_no_array.lower() in [
        u'bit varying',
        u'"char"',
        u'character varying',
        u'double precision',
        u'timestamp without time zone',
        u'timestamp with time zone',
        u'time without time zone',
        u'time with time zone',
        u'"trigger"',
        u'"unknown"'
    ]:
        return False

    # If already quoted?, If yes then do not quote again
    if for_types and val_no_array:
        if val_no_array.startswith('"') \
                or val_no_array.endswith('"'):
            return False

    if u'0' <= val_no_array[0] <= u'9':
        return True

    for c in val_no_array:
        if (not (u'a' <= c <= u'z') and c != u'_' and
                not (u'0' <= c <= u'9')):
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
    return (key in _EXTRA_KEYWORDS and _EXTRA_KEYWORDS[key]) or _KEYWORD_DICT.get(key)


# UNRESERVED_KEYWORD      0
# COL_NAME_KEYWORD        1
# TYPE_FUNC_NAME_KEYWORD  2
# RESERVED_KEYWORD        3
_EXTRA_KEYWORDS = {
    'connect': 3,
    'convert': 3,
    'distributed': 0,
    'exec': 3,
    'log': 0,
    'long': 3,
    'minus': 3,
    'nocache': 3,
    'number': 3,
    'package': 3,
    'pls_integer': 3,
    'raw': 3,
    'return': 3,
    'smalldatetime': 3,
    'smallfloat': 3,
    'smallmoney': 3,
    'sysdate': 3,
    'systimestap': 3,
    'tinyint': 3,
    'tinytext': 3,
    'varchar2': 3
}

# ScanKeyword function for PostgreSQL 9.5rc1
_KEYWORD_DICT = {
    "abort": 0, "absolute": 0, "access": 0, "action": 0, "add": 0, "admin": 0, "after": 0, "aggregate": 0, "all": 3,
    "also": 0, "alter": 0, "always": 0, "analyze": 3, "and": 3, "any": 3, "array": 3, "as": 3, "asc": 3,
    "assertion": 0, "assignment": 0, "asymmetric": 3, "at": 0, "attribute": 0, "authorization": 2, "backward": 0,
    "before": 0, "begin": 0, "between": 1, "bigint": 1, "binary": 2, "bit": 1, "boolean": 1, "both": 3, "by": 0,
    "cache": 0, "called": 0, "cascade": 0, "cascaded": 0, "case": 3, "cast": 3, "catalog": 0, "chain": 0, "char": 1,
    "character": 1, "characteristics": 0, "check": 3, "checkpoint": 0, "class": 0, "close": 0, "cluster": 0,
    "coalesce": 1, "collate": 3, "collation": 2, "column": 3, "comment": 0, "comments": 0, "commit": 0,
    "committed": 0, "concurrently": 2, "configuration": 0, "conflict": 0, "connection": 0, "constraint": 3,
    "constraints": 0, "content": 0, "continue": 0, "conversion": 0, "copy": 0, "cost": 0, "create": 3, "cross": 2,
    "csv": 0, "cube": 0, "current": 0, "current_catalog": 3, "current_date": 3, "current_role": 3,
    "current_schema": 2, "current_time": 3, "current_timestamp": 3, "current_user": 3, "cursor": 0, "cycle": 0,
    "data": 0, "database": 0, "day": 0, "deallocate": 0, "dec": 1, "decimal": 1, "declare": 0, "default": 3,
    "defaults": 0, "deferrable": 3, "deferred": 0, "definer": 0, "delete": 0, "delimiter": 0, "delimiters": 0,
    "desc": 3, "dictionary": 0, "disable": 0, "discard": 0, "distinct": 3, "do": 3, "document": 0, "domain": 0,
    "double": 0, "drop": 0, "each": 0, "else": 3, "enable": 0, "encoding": 0, "encrypted": 0, "end": 3, "enum": 0,
    "escape": 0, "event": 0, "except": 3, "exclude": 0, "excluding": 0, "exclusive": 0, "execute": 0, "exists": 1,
    "explain": 0, "extension": 0, "external": 0, "extract": 1, "false": 3, "family": 0, "fetch": 3, "filter": 0,
    "first": 0, "float": 1, "following": 0, "for": 3, "force": 0, "foreign": 3, "forward": 0, "freeze": 2,
    "from": 3, "full": 2, "function": 0, "functions": 0, "global": 0, "grant": 3, "granted": 0, "greatest": 1,
    "group": 3, "grouping": 1, "handler": 0, "having": 3, "header": 0, "hold": 0, "hour": 0, "identity": 0, "if": 0,
    "ilike": 2, "immediate": 0, "immutable": 0, "implicit": 0, "import": 0, "in": 3, "including": 0, "increment": 0,
    "index": 0, "indexes": 0, "inherit": 0, "inherits": 0, "initially": 3, "inline": 0, "inner": 2, "inout": 1,
    "input": 0, "insensitive": 0, "insert": 0, "instead": 0, "int": 1, "integer": 1, "intersect": 3, "interval": 1,
    "into": 3, "invoker": 0, "is": 2, "isnull": 2, "isolation": 0, "join": 2, "key": 0, "label": 0, "language": 0,
    "large": 0, "last": 0, "lateral": 3, "leading": 3, "leakproof": 0, "least": 1, "left": 2, "level": 0, "like": 2,
    "limit": 3, "listen": 0, "load": 0, "local": 0, "localtime": 3, "localtimestamp": 3, "location": 0, "lock": 0,
    "locked": 0, "logged": 0, "mapping": 0, "match": 0, "materialized": 0, "maxvalue": 0, "minute": 0,
    "minvalue": 0, "mode": 0, "month": 0, "move": 0, "name": 0, "names": 0, "national": 1, "natural": 2, "nchar": 1,
    "next": 0, "no": 0, "none": 1, "not": 3, "nothing": 0, "notify": 0, "notnull": 2, "nowait": 0, "null": 3,
    "nullif": 1, "nulls": 0, "numeric": 1, "object": 0, "of": 0, "off": 0, "offset": 3, "oids": 0, "on": 3,
    "only": 3, "operator": 0, "option": 0, "options": 0, "or": 3, "order": 3, "ordinality": 0, "out": 1, "outer": 2,
    "over": 0, "overlaps": 2, "overlay": 1, "owned": 0, "owner": 0, "parser": 0, "partial": 0, "partition": 0,
    "passing": 0, "password": 0, "placing": 3, "plans": 0, "policy": 0, "position": 1, "preceding": 0,
    "precision": 1, "prepare": 0, "prepared": 0, "preserve": 0, "primary": 3, "prior": 0, "privileges": 0,
    "procedural": 0, "procedure": 0, "program": 0, "quote": 0, "range": 0, "read": 0, "real": 1, "reassign": 0,
    "recheck": 0, "recursive": 0, "ref": 0, "references": 3, "refresh": 0, "reindex": 0, "relative": 0,
    "release": 0, "rename": 0, "repeatable": 0, "replace": 0, "replica": 0, "reset": 0, "restart": 0, "restrict": 0,
    "returning": 3, "returns": 0, "revoke": 0, "right": 2, "role": 0, "rollback": 0, "rollup": 0, "row": 1,
    "rows": 0, "rule": 0, "savepoint": 0, "schema": 0, "scroll": 0, "search": 0, "second": 0, "security": 0,
    "select": 3, "sequence": 0, "sequences": 0, "serializable": 0, "server": 0, "session": 0, "session_user": 3,
    "set": 0, "setof": 1, "sets": 0, "share": 0, "show": 0, "similar": 2, "simple": 0, "skip": 0, "smallint": 1,
    "snapshot": 0, "some": 3, "sql": 0, "stable": 0, "standalone": 0, "start": 0, "statement": 0, "statistics": 0,
    "stdin": 0, "stdout": 0, "storage": 0, "strict": 0, "strip": 0, "substring": 1, "symmetric": 3, "sysid": 0,
    "system": 0, "table": 3, "tables": 0, "tablesample": 2, "tablespace": 0, "temp": 0, "template": 0,
    "temporary": 0, "text": 0, "then": 3, "time": 1, "timestamp": 1, "to": 3, "trailing": 3, "transaction": 0,
    "transform": 0, "treat": 1, "trigger": 0, "trim": 1, "true": 3, "truncate": 0, "trusted": 0, "type": 0,
    "types": 0, "unbounded": 0, "uncommitted": 0, "unencrypted": 0, "union": 3, "unique": 3, "unknown": 0,
    "unlisten": 0, "unlogged": 0, "until": 0, "update": 0, "user": 3, "using": 3, "vacuum": 0, "valid": 0,
    "validate": 0, "validator": 0, "value": 0, "values": 1, "varchar": 1, "variadic": 3, "varying": 0, "verbose": 2,
    "version": 0, "view": 0, "views": 0, "volatile": 0, "when": 3, "where": 3, "whitespace": 0, "window": 3,
    "with": 3, "within": 0, "without": 0, "work": 0, "wrapper": 0, "write": 0, "xml": 0, "xmlattributes": 1,
    "xmlconcat": 1, "xmlelement": 1, "xmlexists": 1, "xmlforest": 1, "xmlparse": 1, "xmlpi": 1, "xmlroot": 1,
    "xmlserialize": 1, "year": 0, "yes": 0, "zone": 0
}
