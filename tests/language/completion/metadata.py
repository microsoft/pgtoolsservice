# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import operator

def compare_result_and_correct_result(test, result, correct_result):
    test.assertListEqual(sorted(result, key=operator.attrgetter("display")), sorted(correct_result, key=operator.attrgetter("display")))
