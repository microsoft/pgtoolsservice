# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import operator
import re
from collections import namedtuple, defaultdict, OrderedDict
from itertools import count, repeat, chain      # noqa
from logging import Logger  # noqa
from prompt_toolkit.completion import Completer, Completion
from typing import List

from ossdbtoolsservice.language.completion.mysql_completion import MySQLCompletion
from .packages.sqlcompletion import (   # noqa
    FromClauseItem, suggest_type, Database, Schema, Table, Function, Column, View,
    Keyword, NamedQuery, Datatype, Alias, Path, JoinCondition, Join
)
from .packages.parseutils.meta import ColumnMetadata, ForeignKey
from .packages.parseutils.utils import last_word
from .packages.mysqlliterals.main import get_literals
from .packages.prioritization import PrevalenceCounter

Match = namedtuple('Match', ['completion', 'priority'])

_Candidate = namedtuple(
    'Candidate', 'completion prio meta synonyms prio2 display schema'
)

# Used to strip trailing '::some_type' from default-value expressions
arg_default_type_strip_regex = re.compile(r'::[\w\.]+(\[\])?$')


def normalize_ref(ref):
    return ref if ref[0] == '"' else '"' + ref.lower() + '"'


def generate_alias(tbl):
    """ Generate a table alias, consisting of all upper-case letters in
    the table name, or, if there are no upper-case letters, the first letter +
    all letters preceded by _
    param tbl - unescaped name of the table to alias
    """
    return ''.join([letter for letter in tbl if letter.isupper()] or
                   [letter for letter, prev in zip(tbl, '_' + tbl) if prev == '_' and letter != '_'])


class MySQLCompleter(Completer):
    # keywords_tree: A dict mapping keywords to well known following keywords.
    # e.g. 'CREATE': ['TABLE', 'USER', ...],
    keywords_tree = get_literals('keywords', type_=dict)
    keywords = tuple(set(chain(keywords_tree.keys(), *keywords_tree.values())))
    functions = get_literals('functions')
    datatypes = get_literals('datatypes')
    reserved_words = set(get_literals('reserved'))

    def __init__(self, smart_completion=True, logger=None, settings=None):
        super(MySQLCompleter, self).__init__()
        self.smart_completion = smart_completion
        self.logger: Logger = logger
        self.prioritizer = PrevalenceCounter()
        settings = settings or {}
        self.signature_arg_style = settings.get(
            'signature_arg_style', '{arg_name} {arg_type}'
        )
        self.call_arg_style = settings.get(
            'call_arg_style', '{arg_name: <{max_arg_len}} := {arg_default}'
        )
        self.call_arg_display_style = settings.get(
            'call_arg_display_style', '{arg_name}'
        )
        self.call_arg_oneliner_max = settings.get('call_arg_oneliner_max', 2)

        keyword_casing = settings.get('keyword_casing', 'upper').lower()
        if keyword_casing not in ('upper', 'lower', 'auto'):
            keyword_casing = 'upper'
        self.keyword_casing = keyword_casing
        self.name_pattern = re.compile(r"^[_a-z][_a-z0-9\$]*$")

        self.databases = []
        self.dbmetadata = {'tables': {}, 'views': {}, 'functions': {},
                           'datatypes': {}}
        self.casing = {}

        self.all_completions = set(self.keywords + self.functions)

    def _log(self, is_error: bool, msg: str, *args) -> None:
        if self.logger is not None:
            if is_error:
                self.logger.error(msg, *args)
            else:
                self.logger.debug(msg, *args)

    def escape_name(self, name):
        if name and ((not self.name_pattern.match(name))
                     or (name.upper() in self.reserved_words)
                     or (name.upper() in self.functions)):
            name = '"%s"' % name

        return name

    def escape_schema(self, name):
        return "'{}'".format(self.unescape_name(name))

    def unescape_name(self, name):
        """ Unquote a string."""
        if name and name[0] == '"' and name[-1] == '"':
            name = name[1:-1]

        return name

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
        metadata = self.dbmetadata['tables']
        for schema in schemata:
            metadata[schema] = {}

        # dbmetadata.values() are the 'tables' and 'functions' dicts
        for metadata in self.dbmetadata.values():
            for schema in schemata:
                metadata[schema] = {}

        self.all_completions.update(schemata)

    def extend_casing(self, words):
        """ extend casing data

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
                self._log(True, '%r %r listed in unrecognized schema %r',
                          kind, relname, schema)
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
            (schema, relname, colname) = self.escaped_names(
                [schema, relname, colname])
            column = ColumnMetadata(
                name=colname,
                datatype=datatype,
                has_default=has_default,
                default=default
            )
            metadata[schema][relname][colname] = column
            self.all_completions.add(colname)

    def extend_functions(self, func_data):

        # func_data is a list of function metadata namedtuples

        # dbmetadata['schema_name']['functions']['function_name'] should return
        # the function metadata namedtuple for the corresponding function
        metadata = self.dbmetadata['functions']

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
                for sch, funcs in self.dbmetadata['functions'].items()
                for func, metas in funcs.items()
                for meta in metas
            }
            for usage in ('call', 'call_display', 'signature')
        }

    def extend_foreignkeys(self, fk_data):

        # fk_data is a list of ForeignKey namedtuples, with fields
        # parentschema, childschema, parenttable, childtable,
        # parentcolumns, childcolumns

        # These are added as a list of ForeignKey namedtuples to the
        # ColumnMetadata namedtuple for both the child and parent
        meta = self.dbmetadata['tables']

        for fk in fk_data:
            e = self.escaped_names
            parentschema, childschema = e([fk.parentschema, fk.childschema])
            parenttable, childtable = e([fk.parenttable, fk.childtable])
            childcol, parcol = e([fk.childcolumn, fk.parentcolumn])
            childcolmeta = meta[childschema][childtable][childcol]
            parcolmeta = meta[parentschema][parenttable][parcol]
            fk = ForeignKey(parentschema, parenttable, parcol,
                            childschema, childtable, childcol)
            childcolmeta.foreignkeys.append((fk))
            parcolmeta.foreignkeys.append((fk))

    def extend_datatypes(self, type_data):

        # dbmetadata['datatypes'][schema_name][type_name] should store type
        # metadata, such as composite type field names. Currently, we're not
        # storing any metadata beyond typename, so just store None
        meta = self.dbmetadata['datatypes']

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
        pass

    def reset_completions(self):
        self.databases = []
        self.special_commands = []
        self.dbmetadata = {'tables': {}, 'views': {}, 'functions': {},
                           'datatypes': {}}
        self.all_completions = set(self.keywords + self.functions)

    def find_matches(self, text, collection, mode='fuzzy', meta=None):
        """Find completion matches for the given text.

        Given the user's input text and a collection of available
        completions, find completions matching the last word of the
        text.

        `collection` can be either a list of strings or a list of Candidate
        namedtuples.
        `mode` can be either 'fuzzy', or 'strict'
            'fuzzy': fuzzy matching, ties broken by name prevalance
            `keyword`: start only matching, ties broken by keyword prevalance

        yields prompt_toolkit Completion instances for any matches found
        in the collection of available completions.

        """
        if not collection:
            return []
        prio_order = [
            'keyword', 'function', 'view', 'table', 'datatype', 'database',
            'schema', 'column', 'table alias', 'join', 'name join', 'fk join'
        ]
        type_priority = prio_order.index(meta) if meta in prio_order else -1
        text = last_word(text, include='most_punctuations').lower()
        text_len = len(text)

        if text and text[0] == '"':
            # text starts with double quote; user is manually escaping a name
            # Match on everything that follows the double-quote. Note that
            # text_len is calculated before removing the quote, so the
            # Completion.position value is correct
            text = text[1:]

        if mode == 'fuzzy':
            fuzzy = True
            priority_func = self.prioritizer.name_count
        else:
            fuzzy = False
            priority_func = self.prioritizer.keyword_count

        # Construct a `_match` function for either fuzzy or non-fuzzy matching
        # The match function returns a 2-tuple used for sorting the matches,
        # or None if the item doesn't match
        # Note: higher priority values mean more important, so use negative
        # signs to flip the direction of the tuple
        if fuzzy:
            regex = '.*?'.join(map(re.escape, text))
            pat = re.compile('(%s)' % regex)

            def _match(item):
                if item.lower()[:len(text) + 1] in (text, text + ' '):
                    # Exact match of first word in suggestion
                    # This is to get exact alias matches to the top
                    # E.g. for input `e`, 'Entries E' should be on top
                    # (before e.g. `EndUsers EU`)
                    return float('Infinity'), -1
                r = pat.search(self.unescape_name(item.lower()))
                if r:
                    return -len(r.group()), -r.start()
        else:
            match_end_limit = len(text)

            def _match(item):
                match_point = item.lower().find(text, 0, match_end_limit)
                if match_point >= 0:
                    # Use negative infinity to force keywords to sort after all
                    # fuzzy matches
                    return -float('Infinity'), -match_point

        matches = []
        for cand in collection:
            if isinstance(cand, _Candidate):
                item, prio, display_meta, synonyms, prio2, display, schema = cand
                if display_meta is None:
                    display_meta = meta
                syn_matches = (_match(x) for x in synonyms)
                # Nones need to be removed to avoid max() crashing in Python 3
                syn_matches = [m for m in syn_matches if m]
                sort_key = max(syn_matches) if syn_matches else None
            else:
                item, display_meta, prio, prio2, display, schema = cand, meta, 0, 0, cand, cand
                sort_key = _match(cand)

            if sort_key:
                if display_meta and len(display_meta) > 50:
                    # Truncate meta-text to 50 characters, if necessary
                    display_meta = display_meta[:47] + u'...'

                # Lexical order of items in the collection, used for
                # tiebreaking items with the same match group length and start
                # position. Since we use *higher* priority to mean "more
                # important," we use -ord(c) to prioritize "aa" > "ab" and end
                # with 1 to prioritize shorter strings (ie "user" > "users").
                # We first do a case-insensitive sort and then a
                # case-sensitive one as a tie breaker.
                # We also use the unescape_name to make sure quoted names have
                # the same priority as unquoted names.
                lexical_priority = (tuple(0 if c in (' _') else -ord(c)
                                          for c in self.unescape_name(item.lower())) + (1,)
                                    + tuple(c for c in item))

                item = self.case(item)
                display = self.case(display)
                priority = (
                    sort_key, type_priority, prio, priority_func(item),
                    prio2, lexical_priority
                )

                extend_completion = MySQLCompletion(
                    text=item,
                    start_position=-text_len,
                    display_meta=display_meta,
                    display=display,
                    schema=schema)

                matches.append(
                    Match(
                        completion=extend_completion,
                        priority=priority
                    )
                )
        return matches

    def case(self, word):
        return self.casing.get(word, word)

    def get_completions(self, document, complete_event, smart_completion=None) -> List[Completion]:
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        if smart_completion is None:
            smart_completion = self.smart_completion

        # If smart_completion is off then match any word that starts with
        # 'word_before_cursor'.
        if not smart_completion:
            matches = self.find_matches(word_before_cursor, self.all_completions,
                                        mode='strict')
            completions = [m.completion for m in matches]
            return sorted(completions, key=operator.attrgetter('text'))

        matches = []
        suggestions = suggest_type(document.text, document.text_before_cursor)

        for suggestion in suggestions:
            suggestion_type = type(suggestion)
            self._log(False, 'Suggestion type: %r', suggestion_type)

            # Map suggestion type to method
            # e.g. 'table' -> self.get_table_matches
            matcher = self.suggestion_matchers.get(suggestion_type)
            if matcher:
                matches.extend(matcher(self, suggestion, word_before_cursor))

        # Sort matches so highest priorities are first
        matches = sorted(matches, key=operator.attrgetter('priority'),
                         reverse=True)

        return [m.completion for m in matches]


    def _arg_list(self, func, usage):
        """Returns a an arg list string, e.g. `(_foo:=23)` for a func.

        :param func is a FunctionMetadata object
        :param usage is 'call', 'call_display' or 'signature'

        """
        template = {
            'call': self.call_arg_style,
            'call_display': self.call_arg_display_style,
            'signature': self.signature_arg_style
        }[usage]
        args = func.args()
        if not template:
            return '()'
        elif usage == 'call' and len(args) < 2:
            return '()'
        elif usage == 'call' and func.has_variadic():
            return '()'
        multiline = usage == 'call' and len(args) > self.call_arg_oneliner_max
        max_arg_len = max(len(a.name) for a in args) if multiline else 0
        args = (
            self._format_arg(template, arg, arg_num + 1, max_arg_len)
            for arg_num, arg in enumerate(args)
        )
        if multiline:
            return '(' + ','.join('\n    ' + a for a in args if a) + '\n)'
        else:
            return '(' + ', '.join(a for a in args if a) + ')'

    def _format_arg(self, template, arg, arg_num, max_arg_len):
        if not template:
            return None
        if arg.has_default:
            arg_default = 'NULL' if arg.default is None else arg.default
            # Remove trailing ::(schema.)type
            arg_default = arg_default_type_strip_regex.sub('', arg_default)
        else:
            arg_default = ''
        return template.format(
            max_arg_len=max_arg_len,
            arg_name=self.case(arg.name),
            arg_num=arg_num,
            arg_type=arg.datatype,
            arg_default=arg_default
        )

    def get_keyword_matches(self, suggestion, word_before_cursor):
        keywords = self.keywords_tree.keys()
        # Get well known following keywords for the last token. If any, narrow
        # candidates to this list.
        next_keywords = self.keywords_tree.get(suggestion.last_token, [])
        if next_keywords:
            keywords = next_keywords

        casing = self.keyword_casing
        if casing == 'auto':
            if word_before_cursor and word_before_cursor[-1].islower():
                casing = 'lower'
            else:
                casing = 'upper'

        if casing == 'upper':
            keywords = [k.upper() for k in keywords]
        else:
            keywords = [k.lower() for k in keywords]

        return self.find_matches(word_before_cursor, keywords,
                                 mode='strict', meta='keyword')

    suggestion_matchers = {
        Keyword: get_keyword_matches,
    }