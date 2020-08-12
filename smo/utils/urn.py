# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from typing import Tuple


URN_REGEX = re.compile(r'/(\w+)\.(\d+)(/.*)')


def process_urn(urn_path: str) -> Tuple[str, int, str]:
    """
    Processes the first fragment of a URN path
    :param urn_path:
    :return: Tuple as follows:
      str: Class name of the first fragment of the URN path
      int: OID of the object in the first fragment of the URN path
      str: Remaining fragment of the URN path
    """
    match = URN_REGEX.match(urn_path)
    if match is None:
        raise ValueError('The URN is invalid')    # TODO: Localize?
    capture_groups = match.groups()
    return capture_groups[0], int(capture_groups[1]), capture_groups[2]
