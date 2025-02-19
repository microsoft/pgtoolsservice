# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any, Callable

from ossdbtoolsservice.converters.pg_converters import (
    PG_DATATYPE_READER_MAP,
    PG_DATATYPE_WRITER_MAP,
    convert_bytes_to_str,
    convert_str,
)


def get_any_to_bytes_converter(
    type_value: str | None, provider: str
) -> Callable[[Any], bytearray]:
    return PG_DATATYPE_WRITER_MAP.get(type_value or "", convert_str)


def get_bytes_to_any_converter(
    type_value: str | None, provider: str
) -> Callable[[bytes], Any]:
    return PG_DATATYPE_READER_MAP.get(type_value or "", convert_bytes_to_str)
