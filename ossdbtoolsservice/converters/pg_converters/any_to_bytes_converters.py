# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import struct

from ossdbtoolsservice.parsers import datatypes

DECODING_METHOD = 'utf-8'


def convert_bool(value: bool):
    return bytearray(struct.pack("?", value))


def convert_short(value: int):
    """ Range of smallint in Pg is the same with short in c,
    although python type is int, but need to pack the value in short format """
    return bytearray(struct.pack("h", value))


def convert_int(value: int):
    """ Range of integer in Pg is the same with int or long in c,
    we pack the value in int format """
    return bytearray(struct.pack("i", value))


def convert_str(value: str):
    return bytearray(value.encode())


def convert_list(value: list):
    return bytearray(json.dumps(value).encode())


PG_DATATYPE_WRITER_MAP = {
    datatypes.DATATYPE_BOOL: convert_bool,
    datatypes.DATATYPE_SMALLINT: convert_short,
    datatypes.DATATYPE_INTEGER: convert_int,
    datatypes.DATATYPE_OID: convert_int,
    datatypes.DATATYPE_SMALLINT_ARRAY: convert_list,
    datatypes.DATATYPE_TEXT_ARRAY: convert_list,
    datatypes.DATATYPE_POINT_ARRAY: convert_list,
    datatypes.DATATYPE_LINE_ARRAY: convert_list,
    datatypes.DATATYPE_LSEG_ARRAY: convert_list,
    datatypes.DATATYPE_BOX_ARRAY: convert_list,
    datatypes.DATATYPE_PATH_ARRAY: convert_list,
    datatypes.DATATYPE_POLYGON_ARRAY: convert_list,
    datatypes.DATATYPE_CIRCLE_ARRAY: convert_list,
    datatypes.DATATYPE_TSVECTOR_ARRAY: convert_list,
    datatypes.DATATYPE_TSQUERY_ARRAY: convert_list,
    datatypes.DATATYPE_XML_ARRAY: convert_list,
    datatypes.DATATYPE_REGPROC_ARRAY: convert_list,
    datatypes.DATATYPE_REGPROCEDURE_ARRAY: convert_list,
    datatypes.DATATYPE_REGOPER_ARRAY: convert_list,
    datatypes.DATATYPE_REGOPERATOR_ARRAY: convert_list,
    datatypes.DATATYPE_REGCLASS_ARRAY: convert_list,
    datatypes.DATATYPE_REGTYPE_ARRAY: convert_list,
    datatypes.DATATYPE_REGROLE_ARRAY: convert_list,
    datatypes.DATATYPE_REGNAMESPACE_ARRAY: convert_list,
    datatypes.DATATYPE_REGCONFIG_ARRAY: convert_list,
    datatypes.DATATYPE_REGDICTIONARY_ARRAY: convert_list,
    datatypes.DATATYPE_PG_LSN_ARRAY: convert_list
}
