
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import sqlparse
from sqlparse.sql import Identifier
from sqlparse.tokens import Token, Error

def is_open_quote(sql):
    """Returns true if the query contains an unclosed quote"""

    # parsed can contain one or more semi-colon separated commands
    parsed = sqlparse.parse(sql)
    return any(_parsed_is_open_quote(p) for p in parsed)


def _parsed_is_open_quote(parsed):
    # Look for unmatched single quotes, or unmatched dollar sign quotes
    return any(tok.match(Token.Error, ("'", "$")) for tok in parsed.flatten())


def parse_partial_identifier(word):
    """Attempt to parse a (partially typed) word as an identifier

    word may include a schema qualification, like `schema_name.partial_name`
    or `schema_name.` There may also be unclosed quotation marks, like
    `"schema`, or `schema."partial_name`

    :param word: string representing a (partially complete) identifier
    :return: sqlparse.sql.Identifier, or None
    """

    p = sqlparse.parse(word)[0]
    n_tok = len(p.tokens)
    if n_tok == 1 and isinstance(p.tokens[0], Identifier):
        return p.tokens[0]
    elif p.token_next_by(m=(Error, '"'))[1]:
        # An unmatched double quote, e.g. '"foo', 'foo."', or 'foo."bar'
        # Close the double quote, then reparse
        return parse_partial_identifier(word + '"')
    else:
        return None
