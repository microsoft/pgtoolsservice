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

        keyword_casing = settings.get('keyword_casing', 'upper').lower()
        if keyword_casing not in ('upper', 'lower', 'auto'):
            keyword_casing = 'upper'
        self.keyword_casing = keyword_casing

        self.dbmetadata = {'tables': {}, 'views': {}, 'functions': {},
                           'datatypes': {}}
        self.casing = {}
        self.casing_file = settings.get('casing_file')
        self.all_completions = set(self.keywords + self.functions)

    def _log(self, is_error: bool, msg: str, *args) -> None:
        if self.logger is not None:
            if is_error:
                self.logger.error(msg, *args)
            else:
                self.logger.debug(msg, *args)

    def unescape_name(self, name):
        """ Unquote a string."""
        if name and name[0] == '"' and name[-1] == '"':
            name = name[1:-1]

        return name

    def extend_database_names(self, databases):
        pass

    def extend_keywords(self, additional_keywords):
        pass

    def extend_schemata(self, schemata):
        pass

    def extend_casing(self, words):
        """ extend casing data

        :return:
        """
        pass

    def extend_relations(self, data, kind):
        """extend metadata for tables or views.

        :param data: list of (schema_name, rel_name) tuples
        :param kind: either 'tables' or 'views'

        :return:

        """
        pass

    def extend_columns(self, column_data, kind):
        """extend column metadata.

        :param column_data: list of (schema_name, rel_name, column_name,
        column_type, has_default, default) tuples
        :param kind: either 'tables' or 'views'

        :return:

        """
        pass

    def extend_functions(self, func_data):
        pass

    def extend_foreignkeys(self, fk_data):
        pass

    def extend_datatypes(self, type_data):
        pass

    def extend_query_history(self, text, is_init=False):
        pass

    def set_search_path(self, search_path):
        pass

    def reset_completions(self):
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