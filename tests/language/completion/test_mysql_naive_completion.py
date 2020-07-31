# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document

from ossdbtoolsservice.language.completion.mysqlcompleter import MySQLCompleter
from ossdbtoolsservice.language.completion.mysql_completion import MySQLCompletion


class TestNaiveCompletion(unittest.TestCase):
    """Methods for testing non-smart completion"""

    def setUp(self):
        self.completer = MySQLCompleter(smart_completion=False)
        self.complete_event = Mock()

    def test_empty_string_completion(self):
        text = ''
        position = 0
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set(map(Completion, self.completer.all_completions)))

    def test_select_keyword_completion(self):
        text = 'SEL'
        position = len('SEL')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([Completion(text='SELECT', start_position=-3)]))

    def test_function_name_completion(self):
        text = 'SELECT MA'
        position = len('SELECT MA')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))

        # grabbed these completions from mysqlliterals.json
        self.assertSetEqual(result, set([
            Completion(text='MANAGED', start_position=-2),
            Completion(text='MASTER_DELAY', start_position=-2),
            Completion(text='MASTER_SSL_CERT', start_position=-2),
            Completion(text='MAXVALUE', start_position=-2),
            Completion(text='MAX_USER_CONNECTIONS', start_position=-2),
            Completion(text='MASTER_CONNECT_RETRY', start_position=-2),
            Completion(text='MASTER_HEARTBEAT_PERIOD', start_position=-2),
            Completion(text='MAX_QUERIES_PER_HOUR', start_position=-2),
            Completion(text='MASTER_PASSWORD', start_position=-2),
            Completion(text='MASTER_LOG_FILE', start_position=-2),
            Completion(text='MAX', start_position=-2),
            Completion(text='MASTER_TLS_VERSION', start_position=-2),
            Completion(text='MASTER_COMPRESSION_ALGORITHMS', start_position=-2), 
            Completion(text='MASTER_USER', start_position=-2),
            Completion(text='MASTER_AUTO_POSITION', start_position=-2),
            Completion(text='MASTER_SSL_CA', start_position=-2),
            Completion(text='MASTER_SSL_CAPATH', start_position=-2),
            Completion(text='MAX_ROWS', start_position=-2),
            Completion(text='MAKEDATE', start_position=-2),
            Completion(text='MAKETIME', start_position=-2),
            Completion(text='MASTER_LOG_POS', start_position=-2),
            Completion(text='MASTER_PORT', start_position=-2),
            Completion(text='MASTER_POS_WAIT', start_position=-2),
            Completion(text='MASTER_SSL_KEY', start_position=-2),
            Completion(text='MASTER_TLS_CIPHERSUITES', start_position=-2),
            Completion(text='MAX_CONNECTIONS_PER_HOUR', start_position=-2),
            Completion(text='MAX_UPDATES_PER_HOUR', start_position=-2),
            Completion(text='MASTER_SSL_CIPHER', start_position=-2),
            Completion(text='MASTER_SSL_VERIFY_SERVER_CERT', start_position=-2), 
            Completion(text='MAKE_SET', start_position=-2),
            Completion(text='MASTER_HOST', start_position=-2),
            Completion(text='MASTER_PUBLIC_KEY_PATH', start_position=-2),
            Completion(text='MASTER_RETRY_COUNT', start_position=-2),
            Completion(text='MASTER_SSL', start_position=-2),
            Completion(text='MASTER_SSL_CRL', start_position=-2),
            Completion(text='MASTER', start_position=-2),
            Completion(text='MASTER_ZSTD_COMPRESSION_LEVEL', start_position=-2),
            Completion(text='MATCH', start_position=-2),
            Completion(text='MASTER_BIND', start_position=-2),
            Completion(text='MASTER_SSL_CRLPATH', start_position=-2),
            Completion(text='MAX_SIZE', start_position=-2),
            Completion(text='MASTER_SERVER_ID', start_position=-2)]))

    def test_column_name_completion(self):
        text = 'SELECT  FROM users'
        position = len('SELECT ')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set(map(Completion, self.completer.all_completions)))

    def test_alter_well_known_keywords_completion(self):
        text = 'ALTER '
        position = len(text)
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event,
            smart_completion=True))
        # Set comparison: > means "is superset"
        self.assertTrue(result > set([
            Completion(text="DATABASE", display_meta='keyword'),
            Completion(text="TABLE", display_meta='keyword'),
            Completion(text="LOGFILE GROUP", display_meta='keyword'),
        ]))
        self.assertTrue(Completion(text="CREATE", display_meta="keyword") not in result)

    def test_keyword_lower_casing(self):
        new_completer = MySQLCompleter(smart_completion=True, settings={'keyword_casing':'lower'})        
        text = 'SEL'
        position = len('SEL')
        result = set(new_completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([Completion(text='select', start_position=-3)]))

