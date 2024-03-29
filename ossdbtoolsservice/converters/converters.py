# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any, Callable  # noqa

import ossdbtoolsservice.utils as utils
from ossdbtoolsservice.converters.pg_converters import (
    PG_DATATYPE_READER_MAP, PG_DATATYPE_WRITER_MAP, convert_bytes_to_str,
    convert_str)

WRITERS = {
    utils.constants.PG_PROVIDER_NAME: PG_DATATYPE_WRITER_MAP
}

READERS = {
    utils.constants.PG_PROVIDER_NAME: PG_DATATYPE_READER_MAP
}


def get_any_to_bytes_converter(type_value: object, provider: str) -> Callable[[Any], bytearray]:
    writer_map: dict = WRITERS[provider]
    return writer_map.get(type_value, convert_str)


def get_bytes_to_any_converter(type_value: str, provider: str) -> Callable[[bytes], Any]:
    reader_map: dict = READERS[provider]
    return reader_map.get(type_value, convert_bytes_to_str)
