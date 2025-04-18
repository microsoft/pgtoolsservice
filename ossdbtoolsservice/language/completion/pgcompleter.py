# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import operator
import re
from collections import OrderedDict, defaultdict, namedtuple
from itertools import chain, count, repeat  # noqa
from logging import Logger  # noqa

# {{ PGToolsService EDIT }}
# from pgspecial.namedqueries import NamedQueries
from prompt_toolkit.completion import Completer, Completion

# {{ PGToolsService EDIT }}
# from prompt_toolkit.document import Document
# {{ PGToolsService EDIT }}
from ossdbtoolsservice.language.completion.pg_completion import PGCompletion

from .completer import Match, MyCompleter, _Candidate
from .packages.parseutils.meta import ColumnMetadata, ForeignKey
from .packages.parseutils.tables import TableReference
from .packages.parseutils.utils import last_word
from .packages.pgliterals.main import get_literals
from .packages.sqlcompletion import (  # noqa
    Alias,
    Column,
    Database,
    Datatype,
    FromClauseItem,
    Function,
    Join,
    JoinCondition,
    Keyword,
    NamedQuery,
    Path,
    Schema,
    Table,
    View,
    suggest_type,
)

# {{ PGToolsService EDIT }}
# from .config import load_config, config_location

# _logger = logging.getLogger(__name__)

# {{ PGToolsService EDIT }}
# NamedQueries.instance = NamedQueries.from_config(
#     load_config(config_location() + 'config'))

_SchemaObject = namedtuple("SchemaObject", "name schema meta schema_name")


def SchemaObject(name, schema=None, meta=None, schema_name=None):
    """
    schema and schema_name mean to same. However, schema holds a value
    only if completion/intellisense
    need it based on _maybe_schema logic. schema_name always holds a value.
    """
    return _SchemaObject(name, schema, meta, schema_name)


def Candidate(
    completion, prio=None, meta=None, synonyms=None, prio2=None, display=None, schema=None
):
    return _Candidate(
        completion, prio, meta, synonyms or [completion], prio2, display or completion, schema
    )


# Used to strip trailing '::some_type' from default-value expressions
arg_default_type_strip_regex = re.compile(r"::[\w\.]+(\[\])?$")


def normalize_ref(ref):
    return ref if ref[0] == '"' else '"' + ref.lower() + '"'


def generate_alias(tbl):
    """Generate a table alias, consisting of all upper-case letters in
    the table name, or, if there are no upper-case letters, the first letter +
    all letters preceded by _
    param tbl - unescaped name of the table to alias
    """
    return "".join(
        [letter for letter in tbl if letter.isupper()]
        or [letter for letter, prev in zip(tbl, "_" + tbl) if prev == "_" and letter != "_"]
    )


class PGCompleter(Completer, MyCompleter):
    # keywords_tree: A dict mapping keywords to well known following keywords.
    # e.g. 'CREATE': ['TABLE', 'USER', ...],
    keywords_tree = get_literals("keywords", type_=dict)
    keywords = tuple(set(chain(keywords_tree.keys(), *keywords_tree.values())))
    functions = get_literals("functions")
    datatypes = get_literals("datatypes")
    reserved_words = set(get_literals("reserved"))

    def __init__(self, smart_completion=True, logger=None, settings=None):
        super().__init__(PGCompletion)
        self.smart_completion = smart_completion
        self.logger: Logger = logger
        settings = settings or {}
        self.signature_arg_style = settings.get(
            "signature_arg_style", "{arg_name} {arg_type}"
        )
        self.call_arg_style = settings.get(
            "call_arg_style", "{arg_name: <{max_arg_len}} := {arg_default}"
        )
        self.call_arg_display_style = settings.get("call_arg_display_style", "{arg_name}")
        self.call_arg_oneliner_max = settings.get("call_arg_oneliner_max", 2)
        self.search_path_filter = settings.get("search_path_filter")
        self.generate_aliases = settings.get("generate_aliases")
        self.casing_file = settings.get("casing_file")
        self.insert_col_skip_patterns = [
            re.compile(pattern)
            for pattern in settings.get(
                "insert_col_skip_patterns", [r"^now\(\)$", r"^nextval\("]
            )
        ]
        self.generate_casing_file = settings.get("generate_casing_file")
        self.qualify_columns = settings.get("qualify_columns", "if_more_than_one_table")
        self.asterisk_column_order = settings.get("asterisk_column_order", "table_order")

        keyword_casing = settings.get("keyword_casing", "upper").lower()
        if keyword_casing not in ("upper", "lower", "auto"):
            keyword_casing = "upper"
        self.keyword_casing = keyword_casing
        self.name_pattern = re.compile(r"^[_a-z][_a-z0-9\$]*$")

        self.databases = []
        self.dbmetadata = {"tables": {}, "views": {}, "functions": {}, "datatypes": {}}
        self.search_path = []

        self.all_completions = set(self.keywords + self.functions)

    def _log(self, is_error: bool, msg: str, *args) -> None:
        if self.logger is not None:
            if is_error:
                self.logger.error(msg, *args)
            else:
                self.logger.debug(msg, *args)

    def escape_name(self, name):
        if name and (
            (not self.name_pattern.match(name))
            or (name.upper() in self.reserved_words)
            or (name.upper() in self.functions)
        ):
            name = f'"{name}"'

        return name

    def escape_schema(self, name):
        return f"'{self.unescape_name(name)}'"

    def escaped_names(self, names):
        return [self.escape_name(name) for name in names]

    def extend_database_names(self, databases):
        databases = self.escaped_names(databases)
        self.databases.extend(databases)

    def extend_keywords(self, additional_keywords):
        keywords_list = list(self.keywords)
        keywords_list.extend(additional_keywords)
        self.keywords = tuple(keywords_list)
        self.all_completions.update(additional_keywords)

    def extend_schemata(self, schemata):
        # schemata is a list of schema names
        schemata = self.escaped_names(schemata)
        metadata = self.dbmetadata["tables"]
        for schema in schemata:
            metadata[schema] = {}

        # dbmetadata.values() are the 'tables' and 'functions' dicts
        for metadata in self.dbmetadata.values():
            for schema in schemata:
                metadata[schema] = {}

        self.all_completions.update(schemata)

    def extend_casing(self, words):
        """extend casing data

        :return:
        """
        # casing should be a dict {lowercasename:PreferredCasingName}
        self.casing = dict((word.lower(), word) for word in words)

    def extend_relations(self, data, kind):
        """extend metadata for tables or views.

        :param data: list of (schema_name, rel_name) tuples
        :param kind: either 'tables' or 'views'

        :return:

        """

        data = [self.escaped_names(d) for d in data]

        # dbmetadata['tables']['schema_name']['table_name'] should be an
        # OrderedDict {column_name:ColumnMetaData}.
        metadata = self.dbmetadata[kind]
        for schema, relname in data:
            try:
                metadata[schema][relname] = OrderedDict()
            except KeyError:
                self._log(
                    True, "%r %r listed in unrecognized schema %r", kind, relname, schema
                )
            self.all_completions.add(relname)

    def extend_columns(self, column_data, kind):
        """extend column metadata.

        :param column_data: list of (schema_name, rel_name, column_name,
        column_type, has_default, default) tuples
        :param kind: either 'tables' or 'views'

        :return:

        """
        metadata = self.dbmetadata[kind]
        for schema, relname, colname, datatype, has_default, default in column_data:
            (schema, relname, colname) = self.escaped_names([schema, relname, colname])
            column = ColumnMetadata(
                name=colname, datatype=datatype, has_default=has_default, default=default
            )
            metadata[schema][relname][colname] = column
            self.all_completions.add(colname)

    def extend_functions(self, func_data):
        # func_data is a list of function metadata namedtuples

        # dbmetadata['schema_name']['functions']['function_name'] should return
        # the function metadata namedtuple for the corresponding function
        metadata = self.dbmetadata["functions"]

        for f in func_data:
            schema, func = self.escaped_names([f.schema_name, f.func_name])

            if func in metadata[schema]:
                metadata[schema][func].append(f)
            else:
                metadata[schema][func] = [f]

            self.all_completions.add(func)

        self._refresh_arg_list_cache()

    def _refresh_arg_list_cache(self):
        # We keep a cache of {function_usage:{function_metadata: function_arg_list_string}}
        # This is used when suggesting functions, to avoid the latency that would result
        # if we'd recalculate the arg lists each time we suggest functions (in large DBs)
        self._arg_list_cache = {
            usage: {
                meta: self._arg_list(meta, usage)
                for sch, funcs in self.dbmetadata["functions"].items()
                for func, metas in funcs.items()
                for meta in metas
            }
            for usage in ("call", "call_display", "signature")
        }

    def extend_foreignkeys(self, fk_data):
        # fk_data is a list of ForeignKey namedtuples, with fields
        # parentschema, childschema, parenttable, childtable,
        # parentcolumns, childcolumns

        # These are added as a list of ForeignKey namedtuples to the
        # ColumnMetadata namedtuple for both the child and parent
        meta = self.dbmetadata["tables"]

        for fk in fk_data:
            e = self.escaped_names
            parentschema, childschema = e([fk.parentschema, fk.childschema])
            parenttable, childtable = e([fk.parenttable, fk.childtable])
            childcol, parcol = e([fk.childcolumn, fk.parentcolumn])
            childcolmeta = meta[childschema][childtable][childcol]
            parcolmeta = meta[parentschema][parenttable][parcol]
            fk = ForeignKey(
                parentschema, parenttable, parcol, childschema, childtable, childcol
            )
            childcolmeta.foreignkeys.append(fk)
            parcolmeta.foreignkeys.append(fk)

    def extend_datatypes(self, type_data):
        # dbmetadata['datatypes'][schema_name][type_name] should store type
        # metadata, such as composite type field names. Currently, we're not
        # storing any metadata beyond typename, so just store None
        meta = self.dbmetadata["datatypes"]

        for t in type_data:
            schema, type_name = self.escaped_names(t)
            meta[schema][type_name] = None
            self.all_completions.add(type_name)

    def extend_query_history(self, text, is_init=False):
        if is_init:
            # During completer initialization, only load keyword preferences,
            # not names
            self.prioritizer.update_keywords(text)
        else:
            self.prioritizer.update(text)

    def set_search_path(self, search_path):
        self.search_path = self.escaped_names(search_path)

    def reset_completions(self):
        self.databases = []
        self.special_commands = []
        self.search_path = []
        self.dbmetadata = {"tables": {}, "views": {}, "functions": {}, "datatypes": {}}
        self.all_completions = set(self.keywords + self.functions)

    def get_completions(
        self, document, complete_event, smart_completion=None
    ) -> list[Completion]:
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        if smart_completion is None:
            smart_completion = self.smart_completion

        # If smart_completion is off then match any word that starts with
        # 'word_before_cursor'.
        if not smart_completion:
            matches = self.find_matches(
                word_before_cursor, self.all_completions, mode="strict"
            )
            completions = [m.completion for m in matches]
            return sorted(completions, key=operator.attrgetter("text"))

        matches = []
        suggestions = suggest_type(document.text, document.text_before_cursor)

        for suggestion in suggestions:
            suggestion_type = type(suggestion)
            self._log(False, "Suggestion type: %r", suggestion_type)

            # Map suggestion type to method
            # e.g. 'table' -> self.get_table_matches
            matcher = self.suggestion_matchers[suggestion_type]
            matches.extend(matcher(self, suggestion, word_before_cursor))

        # Sort matches so highest priorities are first
        matches = sorted(matches, key=operator.attrgetter("priority"), reverse=True)

        return [m.completion for m in matches]

    def get_column_matches(self, suggestion, word_before_cursor):
        tables = suggestion.table_refs
        do_qualify = (
            suggestion.qualifiable
            and {"always": True, "never": False, "if_more_than_one_table": len(tables) > 1}[
                self.qualify_columns
            ]
        )

        def qualify(col, tbl):
            return (tbl + "." + self.case(col)) if do_qualify else self.case(col)  # noqa

        self._log(False, "Completion column scope: %r", tables)
        scoped_cols = self.populate_scoped_cols(tables, suggestion.local_tables)

        def make_cand(name, ref):
            synonyms = (name, generate_alias(self.case(name)))
            return Candidate(qualify(name, ref), 0, "column", synonyms, schema=None)

        def flat_cols():
            return [make_cand(c.name, t.ref) for t, cols in scoped_cols.items() for c in cols]

        if suggestion.require_last_table:
            # require_last_table is used for 'tb11 JOIN tbl2 USING (...' which should
            # suggest only columns that appear in the last table and one more
            ltbl = tables[-1].ref
            other_tbl_cols = set(
                c.name for t, cs in scoped_cols.items() if t.ref != ltbl for c in cs
            )
            scoped_cols = {
                t: [col for col in cols if col.name in other_tbl_cols]
                for t, cols in scoped_cols.items()
                if t.ref == ltbl
            }
        lastword = last_word(word_before_cursor, include="most_punctuations")
        if lastword == "*":
            if suggestion.context == "insert":

                def filter(col):
                    if not col.has_default:
                        return True
                    return not any(
                        p.match(col.default) for p in self.insert_col_skip_patterns
                    )

                scoped_cols = {
                    t: [col for col in cols if filter(col)] for t, cols in scoped_cols.items()
                }
            if self.asterisk_column_order == "alphabetic":
                for cols in scoped_cols.values():
                    cols.sort(key=operator.attrgetter("name"))
            if (
                lastword != word_before_cursor
                and len(tables) == 1
                and word_before_cursor[-len(lastword) - 1] == "."
            ):
                # User typed x.*; replicate "x." for all columns except the
                # first, which gets the original (as we only replace the "*"")
                sep = ", " + word_before_cursor[:-1]
                collist = sep.join(self.case(c.completion) for c in flat_cols())
            else:
                collist = ", ".join(
                    qualify(c.name, t.ref) for t, cs in scoped_cols.items() for c in cs
                )

            return [
                Match(
                    completion=PGCompletion(collist, -1, display_meta="columns", display="*"),
                    priority=(1, 1, 1),
                )
            ]

        return self.find_matches(word_before_cursor, flat_cols(), meta="column")

    def alias(self, tbl, tbls):
        """Generate a unique table alias
        tbl - name of the table to alias, quoted if it needs to be
        tbls - TableReference iterable of tables already in query
        """
        tbl = self.case(tbl)
        tbls = set(normalize_ref(t.ref) for t in tbls)
        if self.generate_aliases:
            tbl = generate_alias(self.unescape_name(tbl))
        if normalize_ref(tbl) not in tbls:
            return tbl
        elif tbl[0] == '"':
            aliases = ('"' + tbl[1:-1] + str(i) + '"' for i in count(2))
        else:
            aliases = (tbl + str(i) for i in count(2))
        return next(a for a in aliases if normalize_ref(a) not in tbls)

    def get_join_matches(self, suggestion, word_before_cursor):
        tbls = suggestion.table_refs
        cols = self.populate_scoped_cols(tbls)
        # Set up some data structures for efficient access
        qualified = dict((normalize_ref(t.ref), t.schema) for t in tbls)
        ref_prio = dict((normalize_ref(t.ref), n) for n, t in enumerate(tbls))
        refs = set(normalize_ref(t.ref) for t in tbls)
        other_tbls = set((t.schema, t.name) for t in list(cols)[:-1])
        joins = []
        # Iterate over FKs in existing tables to find potential joins
        fks = (
            (fk, rtbl, rcol)
            for rtbl, rcols in cols.items()
            for rcol in rcols
            for fk in rcol.foreignkeys
        )
        col = namedtuple("col", "schema tbl col")
        for fk, rtbl, rcol in fks:
            right = col(rtbl.schema, rtbl.name, rcol.name)
            child = col(fk.childschema, fk.childtable, fk.childcolumn)
            parent = col(fk.parentschema, fk.parenttable, fk.parentcolumn)
            left = child if parent == right else parent
            if suggestion.schema and left.schema != suggestion.schema:
                continue
            c = self.case
            if self.generate_aliases or normalize_ref(left.tbl) in refs:
                lref = self.alias(left.tbl, suggestion.table_refs)
                join = (
                    f"{c(left.tbl)} {lref} ON "
                    f"{lref}.{c(left.col)} = {rtbl.ref}.{c(right.col)}"
                )
            else:
                join = "{0} ON {0}.{1} = {2}.{3}".format(
                    c(left.tbl), c(left.col), rtbl.ref, c(right.col)
                )
            alias = generate_alias(self.case(left.tbl))
            synonyms = [join, f"{alias} ON {alias}.{c(left.col)} = {rtbl.ref}.{c(right.col)}"]
            # Schema-qualify if (1) new table in same schema as old, and old
            # is schema-qualified, or (2) new in other schema, except public
            if not suggestion.schema and (
                qualified[normalize_ref(rtbl.ref)]
                and left.schema == right.schema
                or left.schema not in (right.schema, "public")
            ):
                join = left.schema + "." + join
            prio = ref_prio[normalize_ref(rtbl.ref)] * 2 + (
                0 if (left.schema, left.tbl) in other_tbls else 1
            )
            joins.append(Candidate(join, prio, "join", synonyms=synonyms))

        return self.find_matches(word_before_cursor, joins, meta="join")

    def get_join_condition_matches(self, suggestion, word_before_cursor):
        col = namedtuple("col", "schema tbl col")
        tbls = self.populate_scoped_cols(suggestion.table_refs).items
        cols = [(t, c) for t, cs in tbls() for c in cs]
        try:
            lref = (suggestion.parent or suggestion.table_refs[-1]).ref
            ltbl, lcols = [(t, cs) for (t, cs) in tbls() if t.ref == lref][-1]
        except IndexError:  # The user typed an incorrect table qualifier
            return []
        conds, found_conds = [], set()

        def add_cond(lcol, rcol, rref, prio, meta):
            prefix = "" if suggestion.parent else ltbl.ref + "."
            case = self.case
            cond = prefix + case(lcol) + " = " + rref + "." + case(rcol)
            if cond not in found_conds:
                found_conds.add(cond)
                conds.append(Candidate(cond, prio + ref_prio[rref], meta))

        def list_dict(pairs):  # Turns [(a, b), (a, c)] into {a: [b, c]}
            d = defaultdict(list)
            for pair in pairs:
                d[pair[0]].append(pair[1])
            return d

        # Tables that are closer to the cursor get higher prio
        ref_prio = dict((tbl.ref, num) for num, tbl in enumerate(suggestion.table_refs))
        # Map (schema, table, col) to tables
        coldict = list_dict(((t.schema, t.name, c.name), t) for t, c in cols if t.ref != lref)
        # For each fk from the left table, generate a join condition if
        # the other table is also in the scope
        fks = ((fk, lcol.name) for lcol in lcols for fk in lcol.foreignkeys)
        for fk, lcol in fks:
            left = col(ltbl.schema, ltbl.name, lcol)
            child = col(fk.childschema, fk.childtable, fk.childcolumn)
            par = col(fk.parentschema, fk.parenttable, fk.parentcolumn)
            left, right = (child, par) if left == child else (par, child)
            for rtbl in coldict[right]:
                add_cond(left.col, right.col, rtbl.ref, 2000, "fk join")
        # For name matching, use a {(colname, coltype): TableReference} dict
        coltyp = namedtuple("coltyp", "name datatype")
        col_table = list_dict((coltyp(c.name, c.datatype), t) for t, c in cols)
        # Find all name-match join conditions
        for c in (coltyp(c.name, c.datatype) for c in lcols):
            for rtbl in (t for t in col_table[c] if t.ref != ltbl.ref):
                prio = 1000 if c.datatype in ("integer", "bigint", "smallint") else 0
                add_cond(c.name, c.name, rtbl.ref, prio, "name join")

        return self.find_matches(word_before_cursor, conds, meta="join")

    def get_function_matches(self, suggestion, word_before_cursor, alias=False):
        if suggestion.usage == "from":
            # Only suggest functions allowed in FROM clause
            def filt(f):
                return not f.is_aggregate and not f.is_window
        else:
            alias = False

            def filt(f):
                return True

        arg_mode = {
            "signature": "signature",
            "special": None,
        }.get(suggestion.usage, "call")
        # Function overloading means we way have multiple functions of the same
        # name at this point, so keep unique names only
        funcs = set(
            self._make_cand(f, alias, suggestion, arg_mode)
            for f in self.populate_functions(suggestion.schema, filt)
        )

        matches = self.find_matches(word_before_cursor, funcs, meta="function")

        if not suggestion.schema and not suggestion.usage:
            # also suggest hardcoded functions using startswith matching
            predefined_funcs = self.find_matches(
                word_before_cursor, self.functions, mode="strict", meta="function"
            )
            matches.extend(predefined_funcs)

        return matches

    def get_schema_matches(self, suggestion, word_before_cursor):
        schema_names = self.dbmetadata["tables"].keys()

        # Unless we're sure the user really wants them, hide schema names
        # starting with pg_, which are mostly temporary schemas
        if not word_before_cursor.startswith("pg_"):
            schema_names = [s for s in schema_names if not s.startswith("pg_")]

        if suggestion.quoted:
            schema_names = [self.escape_schema(s) for s in schema_names]

        return self.find_matches(word_before_cursor, schema_names, meta="schema")

    def get_from_clause_item_matches(self, suggestion, word_before_cursor):
        alias = self.generate_aliases
        s = suggestion
        t_sug = Table(s.schema, s.table_refs, s.local_tables)
        v_sug = View(s.schema, s.table_refs)
        f_sug = Function(s.schema, s.table_refs, usage="from")
        return (
            self.get_table_matches(t_sug, word_before_cursor, alias)
            + self.get_view_matches(v_sug, word_before_cursor, alias)
            + self.get_function_matches(f_sug, word_before_cursor, alias)
        )

    def _arg_list(self, func, usage):
        """Returns a an arg list string, e.g. `(_foo:=23)` for a func.

        :param func is a FunctionMetadata object
        :param usage is 'call', 'call_display' or 'signature'

        """
        template = {
            "call": self.call_arg_style,
            "call_display": self.call_arg_display_style,
            "signature": self.signature_arg_style,
        }[usage]
        args = func.args()
        if (
            not template
            or usage == "call"
            and len(args) < 2
            or usage == "call"
            and func.has_variadic()
        ):
            return "()"
        multiline = usage == "call" and len(args) > self.call_arg_oneliner_max
        max_arg_len = max(len(a.name) for a in args) if multiline else 0
        args = (
            self._format_arg(template, arg, arg_num + 1, max_arg_len)
            for arg_num, arg in enumerate(args)
        )
        if multiline:
            return "(" + ",".join("\n    " + a for a in args if a) + "\n)"
        else:
            return "(" + ", ".join(a for a in args if a) + ")"

    def _format_arg(self, template, arg, arg_num, max_arg_len):
        if not template:
            return None
        if arg.has_default:
            arg_default = "NULL" if arg.default is None else arg.default
            # Remove trailing ::(schema.)type
            arg_default = arg_default_type_strip_regex.sub("", arg_default)
        else:
            arg_default = ""
        return template.format(
            max_arg_len=max_arg_len,
            arg_name=self.case(arg.name),
            arg_num=arg_num,
            arg_type=arg.datatype,
            arg_default=arg_default,
        )

    def _make_cand(self, tbl, do_alias, suggestion, arg_mode=None):
        """Returns a Candidate namedtuple.

        :param tbl is a SchemaObject
        :param arg_mode determines what type of arg list to suffix for functions.
        Possible values: call, signature

        """
        cased_tbl = self.case(tbl.name)
        if do_alias:
            alias = self.alias(cased_tbl, suggestion.table_refs)
        synonyms = (cased_tbl, generate_alias(cased_tbl))
        maybe_alias = (" " + alias) if do_alias else ""
        maybe_schema = (self.case(tbl.schema) + ".") if tbl.schema else ""
        suffix = self._arg_list_cache[arg_mode][tbl.meta] if arg_mode else ""
        if arg_mode == "call":
            display_suffix = self._arg_list_cache["call_display"][tbl.meta]
        elif arg_mode == "signature":
            display_suffix = self._arg_list_cache["signature"][tbl.meta]
        else:
            display_suffix = ""
        item = maybe_schema + cased_tbl + suffix + maybe_alias
        display = maybe_schema + cased_tbl + display_suffix + maybe_alias
        prio2 = 0 if tbl.schema else 1
        return Candidate(
            item, synonyms=synonyms, prio2=prio2, display=display, schema=tbl.schema_name
        )

    def get_table_matches(self, suggestion, word_before_cursor, alias=False):
        tables = self.populate_schema_objects(suggestion.schema, "tables")
        tables.extend(SchemaObject(tbl.name) for tbl in suggestion.local_tables)

        # Unless we're sure the user really wants them, don't suggest the
        # pg_catalog tables that are implicitly on the search path
        if not suggestion.schema and (not word_before_cursor.startswith("pg_")):
            tables = [t for t in tables if not t.name.startswith("pg_")]
        tables = [self._make_cand(t, alias, suggestion) for t in tables]
        return self.find_matches(word_before_cursor, tables, meta="table")

    def get_view_matches(self, suggestion, word_before_cursor, alias=False):
        views = self.populate_schema_objects(suggestion.schema, "views")

        if not suggestion.schema and (not word_before_cursor.startswith("pg_")):
            views = [v for v in views if not v.name.startswith("pg_")]
        views = [self._make_cand(v, alias, suggestion) for v in views]
        return self.find_matches(word_before_cursor, views, meta="view")

    def get_alias_matches(self, suggestion, word_before_cursor):
        aliases = suggestion.aliases
        return self.find_matches(word_before_cursor, aliases, meta="table alias")

    def get_database_matches(self, _, word_before_cursor):
        return self.find_matches(word_before_cursor, self.databases, meta="database")

    def get_keyword_matches(self, suggestion, word_before_cursor):
        keywords = self.keywords_tree.keys()
        # Get well known following keywords for the last token. If any, narrow
        # candidates to this list.
        next_keywords = self.keywords_tree.get(suggestion.last_token, [])
        if next_keywords:
            keywords = next_keywords

        casing = self.keyword_casing
        if casing == "auto":
            if word_before_cursor and word_before_cursor[-1].islower():
                casing = "lower"
            else:
                casing = "upper"

        if casing == "upper":
            keywords = [k.upper() for k in keywords]
        else:
            keywords = [k.lower() for k in keywords]

        return self.find_matches(word_before_cursor, keywords, mode="strict", meta="keyword")

    # {{ PGToolsService EDIT }}
    # def get_path_matches(self, _, word_before_cursor):
    #     completer = PathCompleter(expanduser=True)
    #     document = Document(text=word_before_cursor,
    #                         cursor_position=len(word_before_cursor))
    #     for c in completer.get_completions(document, None):
    #         yield Match(completion=c, priority=(0,))

    # def get_special_matches(self, _, word_before_cursor):
    #     if not self.pgspecial:
    #         return []

    #     commands = self.pgspecial.commands
    #     cmds = commands.keys()
    #     cmds = [Candidate(cmd, 0, commands[cmd].description) for cmd in cmds]
    #     return self.find_matches(word_before_cursor, cmds, mode='strict')

    def get_datatype_matches(self, suggestion, word_before_cursor):
        # suggest custom datatypes
        types = self.populate_schema_objects(suggestion.schema, "datatypes")
        types = [self._make_cand(t, False, suggestion) for t in types]
        matches = self.find_matches(word_before_cursor, types, meta="datatype")

        if not suggestion.schema:
            # Also suggest hardcoded types
            matches.extend(
                self.find_matches(
                    word_before_cursor, self.datatypes, mode="strict", meta="datatype"
                )
            )

        return matches

    # {{ PGToolsService EDIT }}
    # def get_namedquery_matches(self, _, word_before_cursor):
    #     return self.find_matches(
    #       word_before_cursor, NamedQueries.instance.list(), meta='named query'
    #     )

    suggestion_matchers = {
        FromClauseItem: get_from_clause_item_matches,
        JoinCondition: get_join_condition_matches,
        Join: get_join_matches,
        Column: get_column_matches,
        Function: get_function_matches,
        Schema: get_schema_matches,
        Table: get_table_matches,
        View: get_view_matches,
        Alias: get_alias_matches,
        Database: get_database_matches,
        Keyword: get_keyword_matches,
        # {{ PGToolsService EDIT }}
        # Special: get_special_matches,
        Datatype: get_datatype_matches,
        # {{ PGToolsService EDIT }}
        # NamedQuery: get_namedquery_matches,
        # Path: get_path_matches,
    }

    def populate_scoped_cols(self, scoped_tbls, local_tbls=()):
        """Find all columns in a set of scoped_tables.

        :param scoped_tbls: list of TableReference namedtuples
        :param local_tbls: tuple(TableMetadata)
        :return: {TableReference:{colname:ColumnMetaData}}

        """
        ctes = dict((normalize_ref(t.name), t.columns) for t in local_tbls)
        columns = OrderedDict()
        meta = self.dbmetadata

        def addcols(schema, rel, alias, reltype, cols):
            tbl = TableReference(schema, rel, alias, reltype == "functions")
            if tbl not in columns:
                columns[tbl] = []
            columns[tbl].extend(cols)

        for tbl in scoped_tbls:
            # Local tables should shadow database tables
            if tbl.schema is None and normalize_ref(tbl.name) in ctes:
                cols = ctes[normalize_ref(tbl.name)]
                addcols(None, tbl.name, "CTE", tbl.alias, cols)
                continue
            schemas = [tbl.schema] if tbl.schema else self.search_path
            for schema in schemas:
                relname = self.escape_name(tbl.name)
                schema = self.escape_name(schema)
                if tbl.is_function:
                    # Return column names from a set-returning function
                    # Get an array of FunctionMetadata objects
                    functions = meta["functions"].get(schema, {}).get(relname)
                    for func in functions or []:
                        # func is a FunctionMetadata object
                        cols = func.fields()
                        addcols(schema, relname, tbl.alias, "functions", cols)
                else:
                    for reltype in ("tables", "views"):
                        cols = meta[reltype].get(schema, {}).get(relname)
                        if cols:
                            cols = cols.values()
                            addcols(schema, relname, tbl.alias, reltype, cols)
                            break

        return columns

    def _get_schemas(self, obj_typ, schema):
        """Returns a list of schemas from which to suggest objects.

        :param schema is the schema qualification input by the user (if any)

        """
        metadata = self.dbmetadata[obj_typ]
        if schema:
            schema = self.escape_name(schema)
            return [schema] if schema in metadata else []
        return self.search_path if self.search_path_filter else metadata.keys()

    def _maybe_schema(self, schema, parent):
        return None if parent or schema in self.search_path else schema

    def populate_schema_objects(self, schema, obj_type):
        """Returns a list of SchemaObjects representing tables or views.

        :param schema is the schema qualification input by the user (if any)

        """

        return [
            SchemaObject(
                name=obj,
                schema=(self._maybe_schema(schema=sch, parent=schema)),
                schema_name=sch,
            )
            for sch in self._get_schemas(obj_type, schema)
            for obj in self.dbmetadata[obj_type][sch]
        ]

    def populate_functions(self, schema, filter_func):
        """Returns a list of function SchemaObjects.

        :param filter_func is a function that accepts a FunctionMetadata
        namedtuple and returns a boolean indicating whether that
        function should be kept or discarded

        """

        # Because of multiple dispatch, we can have multiple functions
        # with the same name, which is why `for meta in metas` is necessary
        # in the comprehensions below
        return [
            SchemaObject(
                name=func, schema=(self._maybe_schema(schema=sch, parent=schema)), meta=meta
            )
            for sch in self._get_schemas("functions", schema)
            for (func, metas) in self.dbmetadata["functions"][sch].items()
            for meta in metas
            if filter_func(meta)
        ]
