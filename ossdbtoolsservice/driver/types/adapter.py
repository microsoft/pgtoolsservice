import psycopg
from psycopg.types.string import TextLoader
from psycopg.types.json import _JsonDumper
from psycopg.types.net import InetLoader
from ipaddress import ip_address, ip_interface

encode_dict = {
    'SQL_ASCII': ['SQL_ASCII', 'raw-unicode-escape'],
    'SQLASCII': ['SQLASCII', 'raw-unicode-escape'],
    # EUC_TW Not availble in Python,
    # so psycopg3 do not support it, we are on our own
    'EUC_TW': ['BIG5', 'big5'],
    'EUCTW': ['BIG5', 'big5'],
    # psycopg3 do not support unicode
    'UNICODE': ['utf-8', 'utf-8']
}

PSYCOPG_SUPPORTED_STRING_DATATYPES = (
    # To cast bytea, interval type
    17, 1186,

    # date, timestamp, timestamp with zone, time without time zone
    1082, 1114, 1184, 1083, 1266
)

PSYCOPG_SUPPORTED_STRING_NUMERIC_DATATYPES = (
    # Real, double precision, numeric, bigint, oid
    700, 701, 1700, 20, 26
)

# int4range, int8range, numrange, daterange tsrange, tstzrange
# OID reference psycopg/lib/_range.py
PSYCOPG_SUPPORTED_RANGE_TYPES = (3904, 3926, 3906, 3912, 3908, 3910)

# int4multirange, int8multirange, nummultirange, datemultirange tsmultirange,
# tstzmultirange[]
PSYCOPG_SUPPORTED_MULTIRANGE_TYPES = (4535, 4451, 4536, 4532, 4533, 4534)

PSYCOPG_SUPPORTED_ARRAY_OF_STRING_DATATYPES = (
    # To cast bytea[] type
    1001,

    # bigint[]
    1016,

    # double precision[], real[]
    1022, 1021,

    # bit[], varbit[]
    1561, 1563,
)

PSYCOPG_SUPPORTED_BUILTIN_ARRAY_DATATYPES = (
    1016, 1005, 1006, 1007, 1021, 1022, 1231,
    1002, 1003, 1009, 1014, 1015, 1014, 1015,
    1000, 1115, 1185, 1183, 1270, 1182, 1187,
    1001, 1028, 1013, 1041, 651, 1040
)

# record, record][]
PSYCOPG_SUPPORTED_RECORD_TYPES = (2249, 2287)

# json, jsonb
# OID reference psycopg/lib/_json.py
PSYCOPG_SUPPORTED_JSON_TYPES = (114, 3802)

# json[], jsonb[]
PSYCOPG_SUPPORTED_JSON_ARRAY_TYPES = (199, 3807)

# INET[], CIDR[]
# OID reference psycopg/lib/_ipaddress.py
PSYCOPG_SUPPORTED_IPADDRESS_ARRAY_TYPES = (1041, 651)

# uuid[], uuid
# OID reference psycopg/lib/extras.py
PSYCOPG_SUPPORTED_IPADDRESS_ARRAY_TYPES = (2951, 2950)

# int4range, int8range, numrange, daterange tsrange, tstzrange
# OID reference psycopg/lib/_range.py
PSYCOPG_SUPPORTED_RANGE_TYPES = (3904, 3926, 3906, 3912, 3908, 3910)

# int4multirange, int8multirange, nummultirange, datemultirange tsmultirange,
# tstzmultirange[]
PSYCOPG_SUPPORTED_MULTIRANGE_TYPES = (4535, 4451, 4536, 4532, 4533, 4534)

# int4range[], int8range[], numrange[], daterange[] tsrange[], tstzrange[]
# OID reference psycopg/lib/_range.py
PSYCOPG_SUPPORTED_RANGE_ARRAY_TYPES = (3905, 3927, 3907, 3913, 3909, 3911, 1270)

# int4multirange[], int8multirange[], nummultirange[],
# datemultirange[] tsmultirange[], tstzmultirange[]
PSYCOPG_SUPPORTED_MULTIRANGE_ARRAY_TYPES = (6155, 6150, 6157, 6151, 6152, 6153)


class pgAdminInetLoader(InetLoader):
    def load(self, data):
        if isinstance(data, memoryview):
            data = bytes(data)

        if b"/" in data:
            return str(ip_interface(data.decode()))
        else:
            return str(ip_address(data.decode()))


class TextLoaderpgAdmin(TextLoader):
    def load(self, data):
        postgres_encoding, python_encoding = get_encoding(
            self.connection.info.encoding)
        if postgres_encoding not in ['SQLASCII', 'SQL_ASCII']:
            # In case of errors while decoding data, instead of raising error
            # replace errors with empty space.
            # Error - utf-8 code'c can not decode byte 0x7f:
            # invalid continuation byte
            if isinstance(data, memoryview):
                return bytes(data).decode(self._encoding, errors='replace')
            else:
                return data.decode(self._encoding, errors='replace')
        else:
            # SQL_ASCII Database
            try:
                if isinstance(data, memoryview):
                    return bytes(data).decode(python_encoding)
                return data.decode(python_encoding)
            except Exception:
                if isinstance(data, memoryview):
                    return bytes(data).decode('UTF-8')
                return data.decode('UTF-8')


class JsonDumperpgAdmin(_JsonDumper):

    def dump(self, obj):
        return self.dumps(obj).encode()


def addAdapters():
    # This registers a unicode type caster for datatype 'RECORD'.
    for typ in PSYCOPG_SUPPORTED_RECORD_TYPES:
        psycopg.adapters.register_loader(typ, TextLoaderpgAdmin)

    for typ in PSYCOPG_SUPPORTED_STRING_DATATYPES + PSYCOPG_SUPPORTED_STRING_NUMERIC_DATATYPES +\
            PSYCOPG_SUPPORTED_RANGE_TYPES + PSYCOPG_SUPPORTED_MULTIRANGE_TYPES +\
            PSYCOPG_SUPPORTED_ARRAY_OF_STRING_DATATYPES:
        psycopg.adapters.register_loader(typ, TextLoaderpgAdmin)

    for typ in PSYCOPG_SUPPORTED_BUILTIN_ARRAY_DATATYPES +\
        PSYCOPG_SUPPORTED_JSON_ARRAY_TYPES + PSYCOPG_SUPPORTED_IPADDRESS_ARRAY_TYPES +\
            PSYCOPG_SUPPORTED_RANGE_ARRAY_TYPES + PSYCOPG_SUPPORTED_MULTIRANGE_ARRAY_TYPES:
        psycopg.adapters.register_loader(typ, TextLoaderpgAdmin)

    for typ in PSYCOPG_SUPPORTED_JSON_TYPES + PSYCOPG_SUPPORTED_JSON_ARRAY_TYPES:
        psycopg.adapters.register_loader(typ, TextLoaderpgAdmin)

    psycopg.adapters.register_loader("inet", pgAdminInetLoader)
    psycopg.adapters.register_loader("cidr", pgAdminInetLoader)
    psycopg.adapters.register_dumper(dict, JsonDumperpgAdmin)


def get_encoding(key):
    """
    :param key: Database Encoding
    :return:
    [Postgres_encoding, Python_encoding] -
    Postgres encoding, Python encoding, type cast encoding
    """
    #
    # Reference: https://www.postgresql.org/docs/11/multibyte.html
    #
    if key == 'ascii':
        key = 'raw_unicode_escape'
    try:
        postgres_encoding = psycopg._encodings.py2pgenc(key).decode()
    except Exception:
        postgres_encoding = 'utf-8'

    python_encoding = psycopg._encodings._py_codecs.get(postgres_encoding,
                                                        'utf-8')

    _dict = encode_dict.get(postgres_encoding.upper(),
                            [postgres_encoding,
                             python_encoding])
    return _dict
