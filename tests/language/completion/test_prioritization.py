# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from ossdbtoolsservice.language.completion.packages.prioritization import PrevalenceCounter


class TestPrioritization(unittest.TestCase):
    """Methods for testing prioritization algorithm"""

    def test_prevalence_counter(self):
        counter = PrevalenceCounter()
        sql = """SELECT * FROM foo WHERE bar GROUP BY baz;
                select * from foo;
                SELECT * FROM foo WHERE bar GROUP
                BY baz"""
        counter.update(sql)

        keywords = ["SELECT", "FROM", "GROUP BY"]
        expected = [3, 3, 2]
        kw_counts = [counter.keyword_count(x) for x in keywords]
        self.assertEqual(kw_counts, expected)
        self.assertEqual(counter.keyword_count("NOSUCHKEYWORD"), 0)

        names = ["foo", "bar", "baz"]
        name_counts = [counter.name_count(x) for x in names]
        self.assertListEqual(name_counts, [3, 2, 2])
