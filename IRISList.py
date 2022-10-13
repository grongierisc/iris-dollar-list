from dataclasses import dataclass
import datetime
import decimal
import math
import struct


@dataclass
class _ListItem(object):
    """
    This class is used to store the information about a list item.
    """

    ITEM_UNDEF = -1;
    ITEM_PLACEHOLDER = 0;
    ITEM_ASCII = 1;
    ITEM_UNICODE = 2;
    ITEM_POSINT = 4;
    ITEM_NEGINT = 5;
    ITEM_POSNUM = 6;
    ITEM_NEGNUM = 7;
    ITEM_DOUBLE = 8;
    ITEM_COMPACT_DOUBLE = 9;
    ITEM_OREF_ASCII = 25;
    ITEM_OREF_UNICODE = 26;

    buffer: bytearray
    list_buffer_end: int = 0
    is_null: bool = False
    is_undefined = False
    type: int = ITEM_PLACEHOLDER
    next_offset: int = 0
    data_offset: int = 0
    data_length: int = 0


class _ListReader(object):

    def __init__(self, bufferarray:bytearray, locale="latin-1"):
        self.list_item = _ListItem(bufferarray)
        self._locale = locale

    def __iter__(self):
        return self

    def __next__(self):
        if self._is_end():
            raise StopIteration
        else:
            return self._get(self.list_item,self._locale)

    def _get(self, item, locale, as_bytes = False, retain_ascii_zero = False):
        if item.is_null:
            return None
        func = self._get_switcher.get(item.type, None)
        if func is None:
            raise Exception("Incorrect list format, unknown type: " + item.type)
        else:
            return func(item.buffer, item.data_offset, item.data_length, locale, as_bytes, retain_ascii_zero)


    def _get_raw_bytes(self, length):
        self.is_null = False
        self.list_item.type = _ListItem.ITEM_PLACEHOLDER
        self.list_item.data_offset = 0
        self.list_item.data_length = 0
        self.list_item.next_offset = self.list_item.next_offset + length
        return self.list_item.buffer[self.list_item.next_offset - length:self.list_item.next_offset]

    def _is_end(self):
        return (self.list_item.next_offset >= self.list_item.list_buffer_end)

    def _get_at_offset(self, offset, as_bytes = False):
        self.list_item.next_offset = offset
        return self._get(self.list_item, self._locale, as_bytes)

    def _move_to_end(self):
        self.list_item.next_offset = self.list_item.list_buffer_end 

    def _get_offset(self):
        return self.list_item.next_offset

    def _next(self):
        return self._get_list_element(self.list_item)

    def _get_output_parameter_list(self, begin, add_null):
        len = self.list_item.next_offset - begin
        offset = 3 if add_null else 0
        ba = bytearray(len + offset)
        if add_null:
            quote_quote = bytearray([3, 1, 0])
            ba = quote_quote
        ba[offset:len] = self.list_item.buffer[begin:len]
        return _ListReader(ba, self._locale)

    def _is_past_last_item(self):
        return (self.list_item.data_offset >= self.list_item.list_buffer_end)

    def _is_undefined(self):
        return (self.list_item.type == _ListItem.ITEM_UNDEF)

    def _next_unless_undefined(self):
        self._next()
        if self._is_past_last_item():
            raise Exception("No more data")
        if self._is_undefined():
            raise Exception("Output/Default parameter not assigned a value")
        return

    def _clear_list(self):
        self.list_item.list_buffer_end = 0
        self.list_item.next_offset = 0
        return

    def _get_list_element(self, item:_ListItem):
        buffer = item.buffer
        offset = item.next_offset
        # if first byte is 0, then length is next 2 bytes
        if buffer[offset] == 0:
            length = buffer[offset + 1] | (buffer[offset + 2] << 8);
            offset += 3
            # if the length is still 0, then the length is the next 4 bytes
            if length == 0:
                length = buffer[offset] | (buffer[offset + 1] << 8) | (buffer[offset + 2] << 16) | (buffer[offset + 3] << 24);
                offset += 4
            item.type = buffer[offset]
            if item.type >= 32 and item.type < 64:
                item.type = item.type-32
            item.data_offset = offset + 1
            item.data_length = length - 1
            item.next_offset = item.data_offset + item.data_length
            item.is_null = False
            item.is_undefined = False
        elif buffer[offset] == 1:
            item.type = _ListItem.ITEM_UNDEF
            if item.type >= 32 and item.type < 64:
                item.type = item.type-32
            item.data_offset = offset + 1
            item.data_length = 0
            item.next_offset = item.data_offset
            item.is_null = True
            item.is_undefined = True
        else:
            item.type = buffer[offset + 1]
            if item.type >= 32 and item.type < 64:
                item.type = item.type-32
            item.data_offset = offset + 2
            item.data_length = buffer[offset] - 2
            item.next_offset = item.data_offset + item.data_length
            item.is_null = (item.type == _ListItem.ITEM_PLACEHOLDER) or ((item.type == _ListItem.ITEM_ASCII) and (item.data_length == 0))
            item.is_undefined = False
        return

    def _get_data_offset(self, buffer, offset):
        if buffer[offset] != 0:
            next_offset = offset + buffer[offset]
        elif buffer[offset + 1] == 0 and buffer[offset + 2] == 0:
            if offset + 6 < len(buffer):
                next_offset = (buffer[offset + 3] | (buffer[offset + 4] << 8) | (buffer[offset + 5] << 16)) + 7
        elif offset + 2 < len(buffer):           
            next_offset = (buffer[offset + 1] | (buffer[offset + 2] << 8)) + 3
        return next_offset

    def _grab_ascii_string(self, buffer, offset, length, locale, as_bytes = False, retain_ascii_zero = False):
        byte_array = buffer[offset:offset+length]
        if not retain_ascii_zero and byte_array == b'\x00':
            return ""
        if as_bytes:
            return bytes(byte_array)
        else:
            return byte_array.decode(locale)

    def _grab_unicode_string(self, buffer, offset, length, *args):
        return buffer[offset:offset+length].decode("utf-16LE")

    def _grab_pos_integer(self, buffer, offset, length, *args):
        number = 0
        for i in range(length):
            number = number*256 + buffer[offset+length-i-1]
        return number

    def _grab_neg_integer(self, buffer, offset, length, *args):
        if length == 0:
            return -1
        if length == 1:
            return (buffer[offset]) - 0x100
        if length == 2:
            return (buffer[offset] | buffer[offset+1]<<8) - 0x10000
        if length == 3:
            return (buffer[offset] | buffer[offset+1]<<8 | buffer[offset+2]<<16) - 0x1000000
        if length == 4:
            return (buffer[offset] | buffer[offset+1]<<8 | buffer[offset+2]<<16 | buffer[offset+3]<<24) - 0x100000000
        if length == 5:
            return (buffer[offset] | buffer[offset+1]<<8 | buffer[offset+2]<<16 | buffer[offset+3]<<24 | buffer[offset+4]<<32) - 0x10000000000
        if length == 6:
            return (buffer[offset] | buffer[offset+1]<<8 | buffer[offset+2]<<16 | buffer[offset+3]<<24 | buffer[offset+4]<<32 | buffer[offset+5]<<40) - 0x1000000000000
        if length == 7:
            return (buffer[offset] | buffer[offset+1]<<8 | buffer[offset+2]<<16 | buffer[offset+3]<<24 | buffer[offset+4]<<32 | buffer[offset+5]<<40 | buffer[offset+6]<<48) - 0x100000000000000
        if length == 8:
            return (buffer[offset] | buffer[offset+1]<<8 | buffer[offset+2]<<16 | buffer[offset+3]<<24 | buffer[offset+4]<<32 | buffer[offset+5]<<40 | buffer[offset+6]<<48 | buffer[offset+7]<<56) - 0x10000000000000000
        raise Exception("Integer out of range")

    def _grab_pos_number(self, buffer, offset, length, *args):
        num = self._grab_pos_integer(buffer, offset + 1, length - 1)
        scale = buffer[offset]
        if scale > 127:
            scale -= 256
        return self.__parse_decimal(scale, num)

    def _grab_neg_number(self, buffer, offset, length, *args):
        num = self._grab_neg_integer(buffer, offset + 1, length - 1)
        scale = buffer[offset]
        if scale > 127:
            scale -= 256
        return self.__parse_decimal(scale, num)

    def _grab_double(self, buffer, offset, length, *args):
        if length != 8: return self.__grab_compact_float(buffer, offset, length)
        return struct.unpack('d', buffer[offset:offset+length])[0]

    def _grab_compact_double(self, buffer, offset, length, *args):
        return struct.unpack('d',b'\x00\x00\x00\x00\x00\x00\x00\x00'[length:]+buffer[offset:offset+length])[0]

    def __grab_compact_float(self, buffer, offset, length):
        return struct.unpack('f',b'\x00\x00\x00\x00'[length:]+buffer[offset:offset+length])[0]

    def _set(self, buffer, offset, data, locale, is_unicode, compact_double):
        func = self._set_switcher.get(type(data), None)
        if func is None:
            raise Exception("Unsupported argument type: " + str(type(data)))
        else:
            return func(buffer, offset, data, locale, is_unicode, compact_double)

    def _set_undefined(self, buffer, offset):
        buffer[offset] = 1
        return offset + 1

    def _set_null(self, buffer, offset):
        return self._stuff_null(buffer, offset)

    def _stuff_null(self, buffer, offset, data = None, *args):
        buffer[offset] = 2
        buffer[offset+1] = _ListItem.ITEM_ASCII
        return offset+2

    def _stuff_bytes(self, buffer, offset, data, *args):
        length = len(data)
        offset = self.__set_list_length_type(buffer, offset, length, _ListItem.ITEM_ASCII)
        buffer[offset:offset+length] = data[0:length]
        offset += length
        return offset

    def _stuff_int(self, buffer, offset, data, locale, is_unicode, *args):
        if data > 0x7fffffffffffffff or data < -0x8000000000000000:
            return self._stuff_str(buffer, offset, str(data), locale=locale, is_unicode=is_unicode)          
        if data == 0:
            return self.__set_list_length_type(buffer, offset, 0, _ListItem.ITEM_POSINT)
        elif data > 0:
            length = self.__get_pos_int_length(data)
            offset = self.__set_list_length_type(buffer, offset, length, _ListItem.ITEM_POSINT)
            offset = self.__stuff_raw_int(buffer, offset, data, length)
            return offset
        else:
            length = self.__get_neg_int_length(data)
            offset = self.__set_list_length_type(buffer, offset, length, _ListItem.ITEM_NEGINT)
            offset = self.__stuff_raw_int(buffer, offset, data, length)
            return offset

    def _stuff_double(self, buffer, offset, data, locale, is_unicode, compact_double):
        if compact_double:
            if data == 0 and math.copysign(1,data) > 0:
                return self.__set_list_length_type(buffer, offset, 0, _ListItem.ITEM_DOUBLE)
            # check if value can be corced to a single-precision value
            # pack('<f') can throw OverFlowError
            if struct.unpack('f', struct.pack('f', data))[0] == data:
                lt = _ListItem.ITEM_DOUBLE
                data_bytes = struct.pack('<f',data)
            else:
                lt = _ListItem.ITEM_COMPACT_DOUBLE
                data_bytes = struct.pack('<d',data)
            length = len(data_bytes)
            #skip zeros
            for i in range(length):
                if data_bytes[i] != 0:
                    break
            offset = self.__set_list_length_type(buffer, offset, length-i, lt)
            for j in range(i,length):
                buffer[offset] = data_bytes[j]
                offset += 1
            return offset
        else: # not compact_double
            data_bytes = struct.pack('<d', data)
            length = len(data_bytes)
            offset = self.__set_list_length_type(buffer, offset, length, _ListItem.ITEM_DOUBLE)
            for i in range(length):
                buffer[offset] = data_bytes[i]
                offset += 1
            return offset

    def _stuff_decimal(self, buffer, offset, data, *args):
        try:
            if math.isnan(data) or math.isinf(data):
                return self._stuff_double(buffer, offset, data, *args)
        except ValueError as e:
            if str(data).lower() == "snan":
                return self._stuff_double(buffer, offset, decimal.Decimal('nan'), *args)
            elif str(data).lower() == "-snan":
                return self._stuff_double(buffer, offset, decimal.Decimal('-nan'), *args)
            else:
                raise e

        bd = data
        scale = -bd.as_tuple()[2]
        unscaled_value = int(bd.scaleb(scale))
        # Truncate the magnitude if it does not fit into a 63 bit value
        if self.__get_bitlength(unscaled_value) > 63:
            bd_rnd = decimal.Context(prec=19, rounding=decimal.ROUND_HALF_UP).create_decimal(bd)
            scale = -bd_rnd.as_tuple()[2]
            unscaled_value = int(bd_rnd.scaleb(scale))
            if self.__get_bitlength(unscaled_value) > 63:
                bd_rnd = decimal.Context(prec=18, rounding=decimal.ROUND_HALF_UP).create_decimal(bd)
                scale = -bd_rnd.as_tuple()[2]
                unscaled_value = int(bd_rnd.scaleb(scale))
                if unscaled_value < 922337203685477581 and unscaled_value > -922337203685477581:
                    unscaled_value = int((decimal.Decimal(unscaled_value)*10).to_integral_exact(rounding=decimal.ROUND_HALF_UP))
                    scale += 1
            if self.__get_bitlength(unscaled_value) > 63:
                raise Exception("Decimal out of range")
        # Round the extend scale values in the 128-145 range
        if scale < -127 or scale > 128:
            if scale > 128:
                prec_adj = -scale + 128
            else:
                prec_adj = -scale - 127
            unscaled_value = int(decimal.Decimal(unscaled_value).scaleb(prec_adj).to_integral(rounding=decimal.ROUND_HALF_UP))
            scale += prec_adj
            if unscaled_value == 0:
                scale = 0
            if self.__get_bitlength(unscaled_value) > 63:
                raise Exception("Decimal out of range")
        # If can store in type 6, 7
        if scale < 129 and scale > -128:
            if unscaled_value >= 0:
                length = self.__get_pos_int_length(unscaled_value)
                offset = self.__set_list_length_type(buffer, offset, length + 1, _ListItem.ITEM_POSNUM)
            else:
                length = self.__get_neg_int_length(unscaled_value)
                offset = self.__set_list_length_type(buffer, offset, length + 1, _ListItem.ITEM_NEGNUM)
            scale = -scale
            if scale < 0:
                scale += 256
            buffer[offset] = scale
            offset += 1
            offset = self.__stuff_raw_int(buffer, offset, unscaled_value, length)
            return offset
        # Out of range for IRIS Numeric SQLType
        return self._stuff_double(buffer, offset, data, *args)

    def _stuff_str(self, buffer, offset, data, locale, is_unicode, *args):
        if type(data)==str and len(data) == 0:
            return self.__stuff_empty_string(buffer, offset)
        is_oref = False
        offset_saved = offset
        offset = self.__stuff_8bit_ascii(buffer, offset, data, is_oref)
        if offset == -1:
            offset = offset_saved
            if is_unicode:
                offset = self.__stuff_unicode(buffer, offset, data, is_oref)
            else:
                offset = self.__stuff_multibyte(buffer, offset, data, is_oref, locale)
        return offset

    def __set_list_length_type(self, buffer, offset, length, type):
        length += 1
        if length < 0xFF:
            length += 1;
            buffer[offset] = length
            buffer[offset + 1] = type
            return offset + 2
        if length <= 0xFFFF:
            buffer[offset] = 0
            buffer[offset + 1] = length & 0xFF
            buffer[offset + 2] = (length >> 8) & 0xFF
            buffer[offset + 3] = type
            return offset + 4
        buffer[offset] = 0;
        buffer[offset + 1] = 0;
        buffer[offset + 2] = 0;
        buffer[offset + 3] = length & 0xFF
        buffer[offset + 4] = (length >> 8) & 0xFF
        buffer[offset + 5] = (length >> 16) & 0xFF
        buffer[offset + 6] = (length >> 24) & 0xFF
        buffer[offset + 7] = type
        return offset + 8

    def __get_pos_int_length(self, data):
        if data <= 0xFF:
            return 1
        if data <= 0xFFFF:
            return 2
        if data <= 0xFFFFFF:
            return 3
        if data <= 0xFFFFFFFF:
            return 4
        if data <= 0xFFFFFFFFFF:
            return 5
        if data <= 0xFFFFFFFFFFFF:
            return 6
        if data <= 0xFFFFFFFFFFFFFF:
            return 7
        if data <= 0xFFFFFFFFFFFFFFFF:
            return 8
        raise Exception("Integer out of range")

    def __get_neg_int_length(self, data):
        if data == -1:
            return 0
        if data >= -0x100:
            return 1
        if data >= -0x10000:
            return 2
        if data >= -0x1000000:
            return 3
        if data >= -0x100000000:
            return 4
        if data >= -0x10000000000:
            return 5
        if data >= -0x1000000000000:
            return 6
        if data >= -0x100000000000000:
            return 7
        if data >= -0x10000000000000000:
            return 8
        raise Exception("Integer out of range")

    def __stuff_raw_int(self, buffer, offset, data, length):
        for i in range(length):
            one_byte = data & 255
            data = data >> 8
            buffer[offset+i] = one_byte
        return offset+length

    def __stuff_empty_string(self, buffer, offset):
        buffer[offset] = 3
        buffer[offset+1] = _ListItem.ITEM_ASCII
        buffer[offset+2] = 0
        return offset+3

    def __stuff_8bit_ascii(self, buffer, offset, data, is_oref):
        try:
            list_type =  _ListItem.ITEM_OREF_ASCII if is_oref else _ListItem.ITEM_ASCII
            length = len(data)
            offset = self.__set_list_length_type(buffer, offset, length, list_type)
            buffer[offset:offset+length] = data.encode("latin-1")
            return offset+length
        except Exception as e:
            return -1

    def __stuff_unicode(self, buffer, offset, data, is_oref):
        list_type =  _ListItem.ITEM_OREF_UNICODE if is_oref else _ListItem.ITEM_UNICODE
        byte_array = bytearray(data,"utf-16LE")
        length = len(byte_array)
        offset = self.__set_list_length_type(buffer, offset, length, list_type)
        buffer[offset:offset+length] = byte_array[0:length]
        return offset+length

    def __stuff_multibyte(self, buffer, offset, data, is_oref, locale):
        list_type =  _ListItem.ITEM_OREF_ASCII if is_oref else _ListItem.ITEM_ASCII
        ascii = data.encode(locale)
        length = len(ascii)
        offset = self.__set_list_length_type(buffer, offset, length, list_type)
        buffer[offset:offset+length] = ascii
        return offset + length

    def __parse_decimal(self, scale, num):
        decstr = str(num) + "E" + str(scale)
        dec = decimal.Decimal(decstr)
        return dec

    def __get_bitlength(self, value):
        if value < 0:
            return (value + 1).bit_length()
        else:
            return value.bit_length()

    _get_switcher = {
        _ListItem.ITEM_ASCII: _grab_ascii_string,
        _ListItem.ITEM_UNICODE: _grab_unicode_string,
        _ListItem.ITEM_POSINT: _grab_pos_integer,
        _ListItem.ITEM_NEGINT: _grab_neg_integer,
        _ListItem.ITEM_POSNUM: _grab_pos_number,
        _ListItem.ITEM_NEGNUM: _grab_neg_number,
        _ListItem.ITEM_DOUBLE: _grab_double,
        _ListItem.ITEM_COMPACT_DOUBLE: _grab_compact_double
    }

    _set_switcher = {
        type(None): _stuff_null,
        bytes: _stuff_bytes,
        bytearray: _stuff_bytes,
        bool: _stuff_int,
        int: _stuff_int,
        float: _stuff_double,
        decimal.Decimal: _stuff_decimal,
        str: _stuff_str
    }

class _ListWriter(object):

    CHUNKSIZE = 256

    HOROLOG_ORDINAL = datetime.date(1840, 12, 31).toordinal()

    _estimate_size_switcher = {
        type(None): 2,
        bool: 3,
        int: 10,
        float: 10,
        decimal.Decimal: 11
    }

    def __init__(self, locale = "latin-1", is_unicode = True, compact_double = False):
        self.buffer = bytearray(self.CHUNKSIZE)
        self.offset = 0
        self._locale = locale
        self._is_unicode = is_unicode
        self._compact_double = compact_double

    def _clear_list(self):
        self.offset = 0

    def _set(self, data, retain_empty_string=False):
        if retain_empty_string and type(data) == str and len(data) == 0:
            self._set_null()
        else:
            self.__check_buffer_size(self.__estimate_size(data))
            self.offset = _ListReader._set(self.buffer, self.offset, data, self._locale, self._is_unicode, self._compact_double)
        return

    def _set_list(self, data):
        if data is None:
            self._set_null()
        else:
            self.__check_buffer_size(data.offset)
            self.offset = _IRISList._stuff_bytes(self.buffer, self.offset, data._get_buffer())

    def _set_undefined(self):
        self.__check_buffer_size(1)
        self.offset = _IRISList._set_undefined(self.buffer, self.offset)

    def _set_null(self):
        self.__check_buffer_size(2)
        self.offset = _IRISList._set_null(self.buffer, self.offset)

    def _set_raw_bytes(self, data):
        length = len(data)
        self.__check_buffer_size(length)
        self.buffer[self.offset:self.offset+length] = data[0:length]
        self.offset = self.offset + length
        return

    def _set_stream(self, stream):
        raise NotImplementedError("Stream functionality not yet available with iris.dbapi")
    
    def _set_date_h(self, date):
        if isinstance(date, datetime.date):
            date_h = date.toordinal() - _ListWriter.HOROLOG_ORDINAL
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

class _IRISList(object):
    """
    This class provides an interface to interact with IRIS $LIST data.
    """

    def __init__(self, buffer = None, locale = "latin-1", is_unicode = True, compact_double = False):
        self._list_data = [_ListItem]
        self._locale = locale
        self._is_unicode = is_unicode
        self.compact_double = compact_double
        try:
            if isinstance(buffer,str):
                # Assume it's a string of hex digits
                buffer.encode(self._locale)
            if isinstance(buffer,_IRISList):
                # Assume it's a list
                buffer = _IRISList(buffer)
            if isinstance(buffer,bytes) or isinstance(buffer,bytearray):
                # Assume it's a byte array
                list_reader = _ListReader(buffer, locale)
                while not list_reader._is_end():
                    value = list_reader._get(True)
                    if value is None and list_reader.list_item.type is not _ListItem.ITEM_UNDEF:
                        value = bytes()
                    self._list_data.append(value)
                return
        except Exception as ex:
            raise ex


    def get(self, index):
        """
        Returns the value at a given index.

        get(index)

        Parameters
        ----------
        index : one-based index of the IRISList.

        Return Value
        ------------
        Returns bytes, Decimal, float, int, str, or IRISList.
        """
        raw_data = self._list_data[index-1]
        if type(raw_data) == iris.IRISList:
            raw_data = raw_data.getBuffer()
        if type(raw_data) == bytes:
            return iris.IRIS._convertToString(raw_data, iris.IRIS.MODE_LIST, self._locale)
        return raw_data

    def getBoolean(self, index):
        """
        Returns the value at a given index as a boolean.

        getBoolean(index)

        Parameters
        ----------
        index : one-based index of the IRISList.

        Return Value
        ------------
        Returns bool.
        """
        raw_data = self._list_data[index-1]
        if type(raw_data) == iris.IRISList:
            raw_data = raw_data.getBuffer()
        return iris.IRIS._convertToBoolean(raw_data, iris.IRIS.MODE_LIST, self._locale)

    def getBytes(self, index):
        """
Returns the value at a given index as bytes.

getBytes(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns bytes.
"""
        raw_data = self._list_data[index-1]
        if type(raw_data) == iris.IRISList:
            return raw_data.getBuffer()
        return iris.IRIS._convertToBytes(raw_data, iris.IRIS.MODE_LIST, self._locale, self._is_unicode)

    def getDecimal(self, index):
        """
Returns the value at a given index as a Decimal.

getDecimal(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns Decimal.
"""
        raw_data = self._list_data[index-1]
        if type(raw_data) == iris.IRISList:
            raw_data = raw_data.getBuffer()
        return iris.IRIS._convertToDecimal(raw_data, iris.IRIS.MODE_LIST, self._locale)

    def getFloat(self, index):
        """
Returns the value at a given index as a float.

getFloat(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns float.
"""
        raw_data = self._list_data[index-1]
        if type(raw_data) == iris.IRISList:
            raw_data = raw_data.getBuffer()
        return iris.IRIS._convertToFloat(raw_data, iris.IRIS.MODE_LIST, self._locale)

    def getInteger(self, index):
        """
Returns the value at a given index as an integer.

getInteger(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns int.
"""
        raw_data = self._list_data[index-1]
        if type(raw_data) == iris.IRISList:
            raw_data = raw_data.getBuffer()
        return iris.IRIS._convertToInteger(raw_data, iris.IRIS.MODE_LIST, self._locale)

    def getString(self, index):
        """
Returns the value at a given index as a string.

getString(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns str.
"""
        raw_data = self._list_data[index-1]
        if type(raw_data) == iris.IRISList:
            raw_data = raw_data.getBuffer()
        return iris.IRIS._convertToString(raw_data, iris.IRIS.MODE_LIST, self._locale)

    def getIRISList(self, index):
        """
Returns the value at a given index as an IRISList.

getBytes(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns IRISList.
"""
        raw_data = self._list_data[index-1]
        if type(raw_data) == iris.IRISList or raw_data == None:
            return raw_data
        return iris.IRISList(iris.IRIS._convertToBytes(raw_data, iris.IRIS.MODE_LIST, self._locale, self._is_unicode), self._locale, self._is_unicode, self.compact_double)

    def add(self, value):
        """
Adds a data element at the end of the IRISList.

add(value)

Parameters
----------
value : value of the data to be added.

Return Value
------------
Returns the current IRISList object.
"""
        self._list_data.append(self._convertToInternal(value))
        return self

    def set(self, index, value):
        """
Change data element at a given index location. If the index is beyond the length of the IRISList, IRISList will be first expanded to that many elements, paded with None elements.

set(index, value)

Parameters
----------
index: index at which the data is set to. index is one-based.
value : value of the data to be added.

Return Value
------------
Returns the current IRISList object.
"""
        if index>len(self._list_data):
            self._list_data.extend([None]*(index-len(self._list_data)))
        self._list_data[index-1] = self._convertToInternal(value)
        return self

    def _convertToInternal(self, value):
        if type(value) == bytearray:
            return bytes(value)
        if type(value) == iris.IRISList:
            if not self.compact_double and value.compact_double:
                raise ValueError("Cannot embed an IRISList with Compact Double enabled into an IRISList with Compact Double disabled")
            return iris.IRISList(value.getBuffer(), value._locale, value._is_unicode, value.compact_double)
        return value

    def remove(self, index):
        """
Remove a data element at a given index location.

remove(index, value)

Parameters
----------
index: index at which the data is to be removed. index is one-based.

Return Value
------------
Returns the current IRISList object.
"""
        del self._list_data[index-1]
        return self

    def size(self):
        """
Return the length of the data buffer

size()

Return Value
------------
Returns int.
"""
        return len(self.getBuffer())

    def count(self):
        """
Return the unmber of data elements in the IRISList.

count()

Return Value
------------
Returns int.
"""
        return len(self._list_data)

    def clear(self):
        """
Clears out all data in the IRISList.

clear()

Return Value
------------
Returns the current IRISList object.
"""
        self._list_data = []
        return self

    def equals(self, irislist2):
        """
Returns a boolean indicate if the IRISList is the same as the IRISList of the argument

equals(irislist2)

Parameters
----------
irislist2: the second IRISList object to which to compare.

Return Value
------------
Returns bool.
"""
        if type(irislist2) != iris.IRISList:
            raise TypeError("Argument must be an instance of iris.IRISList")
        if len(self._list_data) != len(irislist2._list_data):
            return False
        for i in range(len(self._list_data)):
            if self.get(i+1) != irislist2.get(i+1):
                return False
        return True

    def __str__(self):
        display = ""
        for i in range(len(self._list_data)):
            raw_data = self._list_data[i]
            if type(raw_data) == iris.IRISList:
                raw_data = raw_data.__str__()
            elif type(raw_data) == bool:
                raw_data = 1 if raw_data else 0
            if type(raw_data) == bytes:
                try:
                    if len(raw_data) == 0:
                        one_value = "empty"
                    else:
                        one_value = iris.IRISList(raw_data).__str__()
                except Exception:
                    one_value = str(raw_data)
            elif type(raw_data) == str:
                try:
                    if len(raw_data) == 0:
                        one_value = "empty"
                    else:
                        one_value = iris.IRISList(bytes(raw_data,"latin-1")).__str__()
                except Exception:
                    one_value = str(raw_data)
            else:
                one_value = str(raw_data)
            display += one_value + ","
        return "$lb(" + display[0:-1] + ")"

    def getBuffer(self):
        """
Returns a byte array that contains the $LIST format of all the data elements.

getBuffer()

Return Value
------------
Returns bytes.
"""
        list_writer = iris._ListWriter._ListWriter(self._locale, self._is_unicode, self.compact_double)
        for i in range(len(self._list_data)):
            if self._list_data[i] == None:
                list_writer._set_undefined()
            elif type(self._list_data[i]) == iris.IRISList:
                buffer = self._list_data[i].getBuffer()
                list_writer._set(buffer)
            else:
                list_writer._set(self._list_data[i], True)
        return bytes(list_writer._get_buffer())

