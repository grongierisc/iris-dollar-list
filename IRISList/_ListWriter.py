import datetime
import decimal
import _DBList
import dbapi._DBAPI

class _ListWriter(object):

    CHUNKSIZE = 256

    def __init__(self, locale = "latin-1", is_unicode = True, compact_double = False):
        self.buffer = bytearray(self.CHUNKSIZE)
        self.offset = 0
        self._locale = locale
        self._is_unicode = is_unicode
        self._compact_double = compact_double

    def _clear_list(self):
        self.offset = 0

    def _set(self, data, retainEmptyString=False):
        if retainEmptyString and type(data) == str and len(data) == 0:
            self._set_null()
        else:
            self.__check_buffer_size(self.__estimate_size(data))
            self.offset = _DBList._DBList._set(self.buffer, self.offset, data, self._locale, self._is_unicode, self._compact_double)
        return

    def _set_list(self, data):
        if data is None:
            self._set_null()
        else:
            self.__check_buffer_size(data.offset)
            self.offset = _DBList._DBList._stuff_bytes(self.buffer, self.offset, data._get_buffer())

    def _set_undefined(self):
        self.__check_buffer_size(1)
        self.offset = _DBList._DBList._set_undefined(self.buffer, self.offset)

    def _set_null(self):
        self.__check_buffer_size(2)
        self.offset = _DBList._DBList._set_null(self.buffer, self.offset)

    def _set_raw_bytes(self, data):
        length = len(data)
        self.__check_buffer_size(length)
        self.buffer[self.offset:self.offset+length] = data[0:length]
        self.offset = self.offset + length
        return

    def _set_parameter(self, param):
        param_switcher = {
            dbapi._DBAPI.SQLType.LONGVARBINARY: self._set_stream,
            dbapi._DBAPI.SQLType.LONGVARCHAR: self._set_stream,
            dbapi._DBAPI.SQLType.DATE: None,
            dbapi._DBAPI.SQLType.TIME: None,
            dbapi._DBAPI.SQLType.TIMESTAMP: None,
            dbapi._DBAPI.SQLType.TYPE_DATE: None,
            dbapi._DBAPI.SQLType.TYPE_TIME: None,
            dbapi._DBAPI.SQLType.TYPE_TIMESTAMP: None,
            dbapi._DBAPI.SQLType.DATE_HOROLOG: self._set_date_h,
            dbapi._DBAPI.SQLType.TIME_HOROLOG: self._set_time_h,
            dbapi._DBAPI.SQLType.TIMESTAMP_POSIX: self._set_posix
        }
        param_func = param_switcher.get(param.type, None)
        if param_func is None:
            self._set(param.value)
        else:
            param_func(param.value)

    def _set_parameter_type(self, param_type, value):
        param_switcher = {
            dbapi._DBAPI.SQLType.LONGVARBINARY: self._set_stream,
            dbapi._DBAPI.SQLType.LONGVARCHAR: self._set_stream,
            dbapi._DBAPI.SQLType.DATE: None,
            dbapi._DBAPI.SQLType.TIME: None,
            dbapi._DBAPI.SQLType.TIMESTAMP: None,
            dbapi._DBAPI.SQLType.TYPE_DATE: None,
            dbapi._DBAPI.SQLType.TYPE_TIME: None,
            dbapi._DBAPI.SQLType.TYPE_TIMESTAMP: None,
            dbapi._DBAPI.SQLType.DATE_HOROLOG: self._set_date_h,
            dbapi._DBAPI.SQLType.TIME_HOROLOG: self._set_time_h,
            dbapi._DBAPI.SQLType.TIMESTAMP_POSIX: self._set_posix
        }
        param_func = param_switcher.get(param_type, None)
        if param_func is None:
            self._set(value)
        else:
            param_func(value)

    def _set_stream(self, stream):
        raise NotImplementedError("Stream functionality not yet available with dbapi")
    
    HOROLOG_ORDINAL = datetime.date(1840, 12, 31).toordinal()
    def _set_date_h(self, date):
        if isinstance(date, datetime.date):
            date_h = date.toordinal() - HOROLOG_ORDINAL
            self._set(date_h)
        else:
            self._set(date)

    def _set_time_h(self, time):
        if isinstance(time, datetime.time) or isinstance(time, datetime.datetime):
            time_h = 3600 * time.hour + 60 * time.minute + time.second
            self._set(time_h)
        else:
            self._set(time)

    def _set_posix(self, timestamp):
        if isinstance(timestamp, datetime.datetime):
            self._set(timestamp.timestamp())
        else:
            self._set(timestamp)

    def _size(self):
        return self.offset

    def _get_buffer(self):
        return self.buffer[0:self.offset]

    def __estimate_size(self, data):
        if type(data) == int and (data > 0x7fffffffffffffff or data < -0x8000000000000000):
            data = str(data)
        if type(data) is str or type(data) is bytes or type(data) is bytearray:
            estimated = len(data)*2+8
        else:
            estimated = self._estimate_size_switcher.get(type(data), 0)
        return estimated

    def __check_buffer_size(self, additional):
        if self.offset + additional > len(self.buffer):
            size_needed = self.offset + additional
            size_to_allocate = len(self.buffer)*2
            while True:
                if size_to_allocate > size_needed:
                    break
                size_to_allocate = size_to_allocate*2
            new_buffer = bytearray(size_to_allocate)
            new_buffer[0:len(self.buffer)] = self.buffer
            self.buffer = new_buffer
        return

    def _save_current_offset(self):
        self.__saved_offset = self.offset
        return

    def _set_saved_offset_type_as_pass_by_reference(self):
        _DBList._DBList._set_type_as_pass_by_reference(self.buffer, self.__saved_offset)
        return

_ListWriter._estimate_size_switcher = {
    type(None): 2,
    bool: 3,
    int: 10,
    float: 10,
    decimal.Decimal: 11
}
