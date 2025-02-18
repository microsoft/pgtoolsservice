# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import re
from collections import namedtuple

from .packages.parseutils.utils import last_word
from .packages.prioritization import PrevalenceCounter

_Candidate = namedtuple("Candidate", "completion prio meta synonyms prio2 display schema")

Match = namedtuple("Match", ["completion", "priority"])


class MyCompleter:
    def __init__(self, completion):
        self.prioritizer = PrevalenceCounter()
        self.casing = {}
        self.completion = completion

    def unescape_name(self, name):
        """Unquote a string."""
        if name and name[0] == '"' and name[-1] == '"':
            name = name[1:-1]

        return name

    def case(self, word):
        return self.casing.get(word, word)

    def find_matches(self, text, collection, mode="fuzzy", meta=None):
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
            "keyword",
            "function",
            "view",
            "table",
            "datatype",
            "database",
            "schema",
            "column",
            "table alias",
            "join",
            "name join",
            "fk join",
        ]
        type_priority = prio_order.index(meta) if meta in prio_order else -1
        text = last_word(text, include="most_punctuations").lower()
        text_len = len(text)

        if text and text[0] == '"':
            # text starts with double quote; user is manually escaping a name
            # Match on everything that follows the double-quote. Note that
            # text_len is calculated before removing the quote, so the
            # Completion.position value is correct
            text = text[1:]

        if mode == "fuzzy":
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
            regex = ".*?".join(map(re.escape, text))
            pat = re.compile(f"({regex})")

            def _match(item):
                if item.lower()[: len(text) + 1] in (text, text + " "):
                    # Exact match of first word in suggestion
                    # This is to get exact alias matches to the top
                    # E.g. for input `e`, 'Entries E' should be on top
                    # (before e.g. `EndUsers EU`)
                    return float("Infinity"), -1
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
                    return -float("Infinity"), -match_point

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
                item, display_meta, prio, prio2, display, schema = (
                    cand,
                    meta,
                    0,
                    0,
                    cand,
                    cand,
                )
                sort_key = _match(cand)

            if sort_key:
                if display_meta and len(display_meta) > 50:
                    # Truncate meta-text to 50 characters, if necessary
                    display_meta = display_meta[:47] + "..."

                # Lexical order of items in the collection, used for
                # tiebreaking items with the same match group length and start
                # position. Since we use *higher* priority to mean "more
                # important," we use -ord(c) to prioritize "aa" > "ab" and end
                # with 1 to prioritize shorter strings (ie "user" > "users").
                # We first do a case-insensitive sort and then a
                # case-sensitive one as a tie breaker.
                # We also use the unescape_name to make sure quoted names have
                # the same priority as unquoted names.
                lexical_priority = (
                    tuple(
                        0 if c in (" _") else -ord(c)
                        for c in self.unescape_name(item.lower())
                    )
                    + (1,)
                    + tuple(c for c in item)
                )

                item = self.case(item)
                display = self.case(display)
                priority = (
                    sort_key,
                    type_priority,
                    prio,
                    priority_func(item),
                    prio2,
                    lexical_priority,
                )

                extend_completion = self.completion(
                    text=item,
                    start_position=-text_len,
                    display_meta=display_meta,
                    display=display,
                    schema=schema,
                )

                matches.append(Match(completion=extend_completion, priority=priority))
        return matches
