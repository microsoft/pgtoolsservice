# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import operator
from collections import namedtuple, defaultdict, OrderedDict
from itertools import count, repeat, chain      # noqa
from logging import Logger  # noqa
from prompt_toolkit.completion import Completer, Completion
from typing import List

from ossdbtoolsservice.language.completion.mysql_completion import MySQLCompletion
from .completer import MyCompleter
from .packages.sqlcompletion import (   # noqa
    FromClauseItem, suggest_type, Database, Schema, Table, Function, Column, View,
    Keyword, NamedQuery, Datatype, Alias, Path, JoinCondition, Join
)
from .packages.parseutils.meta import ColumnMetadata, ForeignKey
from .packages.mysqlliterals.main import get_literals
from .packages.prioritization import PrevalenceCounter

class MySQLCompleter(Completer, MyCompleter):
    # keywords_tree: A dict mapping keywords to well known following keywords.
    # e.g. 'CREATE': ['TABLE', 'USER', ...],
    keywords_tree = get_literals('keywords', type_=dict)
    keywords = tuple(set(chain(keywords_tree.keys(), *keywords_tree.values())))
    functions = get_literals('functions')
    datatypes = get_literals('datatypes')
    reserved_words = set(get_literals('reserved'))

    def __init__(self, smart_completion=True, logger=None, settings=None):
        super(MySQLCompleter, self).__init__(MySQLCompletion)
        self.smart_completion = smart_completion
        self.logger: Logger = logger
        settings = settings or {}

        keyword_casing = settings.get('keyword_casing', 'upper').lower()
        if keyword_casing not in ('upper', 'lower', 'auto'):
            keyword_casing = 'upper'
        self.keyword_casing = keyword_casing
        self.casing_file = settings.get('casing_file')
        self.all_completions = set(self.keywords + self.functions)

    def _log(self, is_error: bool, msg: str, *args) -> None:
        if self.logger is not None:
            if is_error:
                self.logger.error(msg, *args)
            else:
                self.logger.debug(msg, *args)


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

    def get_function_matches(self, suggestion, word_before_cursor, alias=False):
        matches = self.find_matches(
            word_before_cursor, self.functions, mode='strict',
            meta='function')

        return matches

    suggestion_matchers = {
        Keyword: get_keyword_matches,
        Function: get_function_matches,
    }
