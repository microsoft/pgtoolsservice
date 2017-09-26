# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import struct
from enum import Enum
from typing import Callable # noqa

from pgsqltoolsservice.parsers import datatypes

class FileSeekPositionType(Enum):
    """ enum of args for seek method"""
    Begin = 0
    Current = 1
    End = 2

class ServiceBufferFileStreamWriter:
    """ Writer for service buffer formatted file streams """

    WRITER_STREAM_NONE_ERROR = "stream argument is None"
    WRITER_STREAM_NOT_SUPPORT_WRITING_ERROR = "stream argument doesn't support writing"
    WRITER_DATA_TYPE_NOT_EXIST_ERROR = "data type doesn't exit"
    WRITER_DATA_TYPE_NOT_CHAR_ERROR = "data type is not character"
    WRITER_DATA_WRITE_ERROR = "Data write error"

    def __init__(self, stream) -> None:
        
        if stream is None:
            raise ValueError(ServiceBufferFileStreamWriter.WRITER_STREAM_NONE_ERROR)    
        
        if not stream.writable():
            raise ValueError(ServiceBufferFileStreamWriter.WRITER_STREAM_NOT_SUPPORT_WRITING_ERROR)

        self._file_stream = stream        

        self._close_stream_flag = False

        self._DATATYPE_WRITER_MAP = {
            datatypes.DATATYPE_BOOL: self._write_bool,
            datatypes.DATATYPE_REAL: self._write_float,
            datatypes.DATATYPE_DOUBLE: self._write_float,
            datatypes.DATATYPE_SMALLINT: self._write_int,
            datatypes.DATATYPE_INTEGER: self._write_int,
            datatypes.DATATYPE_BIGINT: self._write_int,
            datatypes.DATATYPE_NUMERIC: self._write_decimal,
            datatypes.DATATYPE_CHAR: self._write_char,
            datatypes.DATATYPE_VARCHAR: self._write_str,
            datatypes.DATATYPE_TEXT: self._write_str,
            datatypes.DATATYPE_DATE: self._write_date,
            datatypes.DATATYPE_TIME: self._write_time,
            datatypes.DATATYPE_TIME_WITH_TIMEZONE: self._write_time_with_timezone,
            datatypes.DATATYPE_TIMESTAMP: self._write_datetime,
            datatypes.DATATYPE_TIMESTAMP_WITH_TIMEZONE: self._write_datetime,
            datatypes.DATATYPE_INTERVAL: self._write_timedelta,
            datatypes.DATATYPE_UUID: self._write_uuid
        }

    def _write_null(self):
        ba=bytearray([])
        return self._write_to_file(self._file_stream, ba)

    def _write_bool(self, val):    
        ba=bytearray(struct.pack("?", val)) 
        return self._write_to_file(self._file_stream, ba)

    def _write_float(self, val):    
        ba = bytearray(struct.pack("f", val))
        return self._write_to_file(self._file_stream, ba)            

    def _write_int(self, val):
        ba=bytearray(struct.pack("i", val))      
        return self._write_to_file(self._file_stream, ba)

    def _write_decimal(self, val):  
        ba=bytearray(struct.pack("i", int(val)))    
        return self._write_to_file(self._file_stream, ba)            

    def _write_char(self, val):
        if len(val) != 1:
            raise ValueError(ServiceBufferFileStreamWriter.WRITER_DATA_TYPE_NOT_CHAR_ERROR)    
        ba = bytearray(val.encode())
        return self._write_to_file(self._file_stream, ba)            

    def _write_str(self, val):    
        ba = bytearray(val.encode())
        return self._write_to_file(self._file_stream, ba)            

    def _write_date(self, val):            
        val_str = val.isoformat() # isoformat is 'YYYY-MM-DD'
        ba = bytearray(val_str.encode())
        return self._write_to_file(self._file_stream, ba)            

    def _write_time(self, val):     
        val_str = val.isoformat() # isoformat is 'HH:MM:SS'
        ba = bytearray(val_str.encode())
        return self._write_to_file(self._file_stream, ba)            

    def _write_time_with_timezone(self, val):   
        ba = bytearray(val.encode())
        return self._write_to_file(self._file_stream, ba)            

    def _write_datetime(self, val):
        val_str = val.isoformat() # isoformat is 'YYYY-MM-DDTHH:MM:SS.mmmmmm'
        ba = bytearray(val_str.encode())
        return self._write_to_file(self._file_stream, ba)            

    def _write_timedelta(self, val):
        val_in_seconds: float = val.total_seconds()   
        ba = bytearray(struct.pack("f", val_in_seconds))
        return self._write_to_file(self._file_stream, ba)            

    def _write_uuid(self, val):
        ba = bytearray(str(val).encode())
        return self._write_to_file(self._file_stream, ba)            

    def _write_to_file(self, stream, byte_array):
        try:
            written_byte_number = stream.write(byte_array)
        except IOError:
            raise IOError(ServiceBufferFileStreamWriter.WRITER_DATA_WRITE_ERROR)
        return written_byte_number

    def _get_data_writer(self, type_val: str) -> Callable[[str], object]:
        return self._DATATYPE_WRITER_MAP[type_val]

    def write_row(self, reader):              
        """   Write a row to a file   """
        # Define a object list to store multiple columns in a row
        len_columns_info = len(reader.columns_info)
        values = [len_columns_info]

        #Loop over all the columns and write the values to the temp file
        rowBytes = 0
        for i in range(0, len_columns_info):
            #If it's the last column data, then set the flag to true and close the file stream
            if i == len_columns_info - 1:
                self._close_stream_flag = True
 
            ci = reader.columns_info[i]        

            values.append(reader.get_value(i))
            type_val = ci.data_type_name

            #write the object into the temp file
            if type_val == datatypes.DATATYPE_NULL:
                rowBytes += self._write_null()
            else:
                if ci.is_sql_variant:
                    #serialize type information as a string before the value
                    rowBytes += self._write_str(str(type_val))

                data_writer = self._get_data_writer(type_val)

                if data_writer is None:
                    raise TypeError(ServiceBufferFileStreamWriter.WRITER_DATA_TYPE_NOT_EXIST_ERROR)

                rowBytes += data_writer(values[i])
            
            if self._close_stream_flag:
                self._file_stream.close()

        return rowBytes
    
    def seek(self, offset):
        self._file_stream.seek(offset, FileSeekPositionType.Begin)
