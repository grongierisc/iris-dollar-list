import struct
import decimal
import functools
import math

class _DBList(object):

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

    @classmethod
    def _get_list_element(cls, item):
        buffer = item.buffer
        offset = item.next_offset
        item.by_reference = False
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
                item.by_reference = True
            item.data_offset = offset + 1
            item.data_length = length - 1
            item.next_offset = item.data_offset + item.data_length
            item.is_null = False
            item.is_undefined = False
        elif buffer[offset] == 1:
            item.type = cls.ITEM_UNDEF
            if item.type >= 32 and item.type < 64:
                item.type = item.type-32
                item.by_reference = True
            item.data_offset = offset + 1
            item.data_length = 0
            item.next_offset = item.data_offset
            item.is_null = True
            item.is_undefined = True
        else:
            item.type = buffer[offset + 1]
            if item.type >= 32 and item.type < 64:
                item.type = item.type-32
                item.by_reference = True
            item.data_offset = offset + 2
            item.data_length = buffer[offset] - 2
            item.next_offset = item.data_offset + item.data_length
            item.is_null = (item.type == cls.ITEM_PLACEHOLDER) or ((item.type == cls.ITEM_ASCII) and (item.data_length == 0))
            item.is_undefined = False
        return

    @classmethod
    def _get_data_offset(cls, buffer, offset):
        if buffer[offset] != 0:
            next_offset = offset + buffer[offset]
        elif buffer[offset + 1] == 0 and buffer[offset + 2] == 0:
            if offset + 6 < len(buffer):
                next_offset = (buffer[offset + 3] | (buffer[offset + 4] << 8) | (buffer[offset + 5] << 16)) + 7
        elif offset + 2 < len(buffer):           
            next_offset = (buffer[offset + 1] | (buffer[offset + 2] << 8)) + 3
        return next_offset

    @classmethod
    def _get(cls, item, locale, asBytes = False, retainAsciiZero = False):
        if item.is_null:
            return None
        func = cls._get_switcher.get(item.type, None)
        if func is None:
            raise Exception("Incorrect list format, unknown type: " + item.type)
        else:
            return func(item.buffer, item.data_offset, item.data_length, locale, asBytes, retainAsciiZero)

    @classmethod
    def _grab_ascii_string(cls, buffer, offset, length, locale, asBytes = False, retainAsciiZero = False):
        byte_array = buffer[offset:offset+length]
        if not retainAsciiZero and byte_array == b'\x00':
            return ""
        if asBytes:
            return bytes(byte_array)
        else:
            return byte_array.decode(locale)

    @classmethod
    def _grab_unicode_string(cls, buffer, offset, length, *args):
        return buffer[offset:offset+length].decode("utf-16LE")

    @classmethod
    def _grab_pos_integer(cls, buffer, offset, length, *args):
        number = 0
        for i in range(length):
            number = number*256 + buffer[offset+length-i-1]
        return number

    @classmethod
    def _grab_neg_integer(cls, buffer, offset, length, *args):
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

    @classmethod
    def _grab_pos_number(cls, buffer, offset, length, *args):
        num = cls._grab_pos_integer(buffer, offset + 1, length - 1)
        scale = buffer[offset]
        if scale > 127:
            scale -= 256
        return cls.__parse_decimal(scale, num)

    @classmethod
    def _grab_neg_number(cls, buffer, offset, length, *args):
        num = cls._grab_neg_integer(buffer, offset + 1, length - 1)
        scale = buffer[offset]
        if scale > 127:
            scale -= 256
        return cls.__parse_decimal(scale, num)

    @classmethod
    def _grab_double(cls, buffer, offset, length, *args):
        if length != 8: return cls.__grab_compact_float(buffer, offset, length)
        return struct.unpack('d', buffer[offset:offset+length])[0]

    @classmethod
    def _grab_compact_double(cls, buffer, offset, length, *args):
        return struct.unpack('d',b'\x00\x00\x00\x00\x00\x00\x00\x00'[length:]+buffer[offset:offset+length])[0]

    @classmethod
    def __grab_compact_float(cls, buffer, offset, length):
        return struct.unpack('f',b'\x00\x00\x00\x00'[length:]+buffer[offset:offset+length])[0]

    @classmethod
    def _grab_oref_ascii(cls, buffer, offset, length, locale, *args):
        return _IRISOREF._IRISOREF(cls._grab_ascii_string(buffer, offset, length, locale, False))

    @classmethod
    def _grab_oref_unicode(cls, buffer, offset, length, *args):
        return _IRISOREF._IRISOREF(cls._grab_unicode_string(buffer, offset, length))

    @classmethod
    def _set(cls, buffer, offset, data, locale, is_unicode, compact_double):
        func = cls._set_switcher.get(type(data), None)
        if func is None:
            raise Exception("Unsupported argument type: " + str(type(data)))
        else:
            return func(buffer, offset, data, locale, is_unicode, compact_double)

    @classmethod
    def _set_undefined(cls, buffer, offset):
        buffer[offset] = 1
        return offset + 1

    @classmethod
    def _set_null(cls, buffer, offset):
        return cls._stuff_null(buffer, offset)

    @classmethod
    def _stuff_null(cls, buffer, offset, data = None, *args):
        buffer[offset] = 2
        buffer[offset+1] = cls.ITEM_ASCII
        return offset+2

    @classmethod
    def _stuff_bytes(cls, buffer, offset, data, *args):
        length = len(data)
        offset = cls.__set_list_length_type(buffer, offset, length, cls.ITEM_ASCII)
        buffer[offset:offset+length] = data[0:length]
        offset += length
        return offset

    @classmethod
    def _stuff_int(cls, buffer, offset, data, locale, is_unicode, *args):
        if data > 0x7fffffffffffffff or data < -0x8000000000000000:
            return cls._stuff_str(buffer, offset, str(data), locale=locale, is_unicode=is_unicode)          
        if data == 0:
            return cls.__set_list_length_type(buffer, offset, 0, cls.ITEM_POSINT)
        elif data > 0:
            length = cls.__get_pos_int_length(data)
            offset = cls.__set_list_length_type(buffer, offset, length, cls.ITEM_POSINT)
            offset = cls.__stuff_raw_int(buffer, offset, data, length)
            return offset
        else:
            length = cls.__get_neg_int_length(data)
            offset = cls.__set_list_length_type(buffer, offset, length, cls.ITEM_NEGINT)
            offset = cls.__stuff_raw_int(buffer, offset, data, length)
            return offset

    @classmethod
    def _stuff_double(cls, buffer, offset, data, locale, is_unicode, compact_double):
        if compact_double:
            if data == 0 and math.copysign(1,data) > 0:
                return cls.__set_list_length_type(buffer, offset, 0, cls.ITEM_DOUBLE)
            # check if value can be corced to a single-precision value
            # pack('<f') can throw OverFlowError
            if struct.unpack('f', struct.pack('f', data))[0] == data:
                lt = cls.ITEM_DOUBLE
                data_bytes = struct.pack('<f',data)
            else:
                lt = cls.ITEM_COMPACT_DOUBLE
                data_bytes = struct.pack('<d',data)
            length = len(data_bytes)
            #skip zeros
            for i in range(length):
                if data_bytes[i] != 0:
                    break
            offset = cls.__set_list_length_type(buffer, offset, length-i, lt)
            for j in range(i,length):
                buffer[offset] = data_bytes[j]
                offset += 1
            return offset
        else: # not compact_double
            data_bytes = struct.pack('<d', data)
            length = len(data_bytes)
            offset = cls.__set_list_length_type(buffer, offset, length, cls.ITEM_DOUBLE)
            for i in range(length):
                buffer[offset] = data_bytes[i]
                offset += 1
            return offset

    @classmethod
    def _stuff_decimal(cls, buffer, offset, data, *args):
        try:
            if math.isnan(data) or math.isinf(data):
                return cls._stuff_double(buffer, offset, data, *args)
        except ValueError as e:
            if str(data).lower() == "snan":
                return cls._stuff_double(buffer, offset, decimal.Decimal('nan'), *args)
            elif str(data).lower() == "-snan":
                return cls._stuff_double(buffer, offset, decimal.Decimal('-nan'), *args)
            else:
                raise e
        bd = data
        scale = -bd.as_tuple()[2]
        unscaled_value = int(bd.scaleb(scale))
        # Truncate the magnitude if it does not fit into a 63 bit value
        if cls.__get_bitlength(unscaled_value) > 63:
            bd_rnd = decimal.Context(prec=19, rounding=decimal.ROUND_HALF_UP).create_decimal(bd)
            scale = -bd_rnd.as_tuple()[2]
            unscaled_value = int(bd_rnd.scaleb(scale))
            if cls.__get_bitlength(unscaled_value) > 63:
                bd_rnd = decimal.Context(prec=18, rounding=decimal.ROUND_HALF_UP).create_decimal(bd)
                scale = -bd_rnd.as_tuple()[2]
                unscaled_value = int(bd_rnd.scaleb(scale))
                if unscaled_value < 922337203685477581 and unscaled_value > -922337203685477581:
                    unscaled_value = int((decimal.Decimal(unscaled_value)*10).to_integral_exact(rounding=decimal.ROUND_HALF_UP))
                    scale += 1
            if cls.__get_bitlength(unscaled_value) > 63:
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
            if cls.__get_bitlength(unscaled_value) > 63:
                raise Exception("Decimal out of range")
        # If can store in type 6, 7
        if scale < 129 and scale > -128:
            if unscaled_value >= 0:
                length = cls.__get_pos_int_length(unscaled_value)
                offset = cls.__set_list_length_type(buffer, offset, length + 1, cls.ITEM_POSNUM)
            else:
                length = cls.__get_neg_int_length(unscaled_value)
                offset = cls.__set_list_length_type(buffer, offset, length + 1, cls.ITEM_NEGNUM)
            scale = -scale
            if scale < 0:
                scale += 256
            buffer[offset] = scale
            offset += 1
            offset = cls.__stuff_raw_int(buffer, offset, unscaled_value, length)
            return offset
        # Out of range for IRIS Numeric SQLType
        return cls._stuff_double(buffer, offset, data, *args)

    @classmethod
    def _stuff_str(cls, buffer, offset, data, locale, is_unicode, *args):
        if type(data)==str and len(data) == 0:
            return cls.__stuff_empty_string(buffer, offset)
        is_oref = False
        if type(data) == _IRISOREF._IRISOREF:
            data = data._oref
            is_oref = True
        offset_saved = offset
        offset = cls.__stuff_8bit_ascii(buffer, offset, data, is_oref)
        if offset == -1:
            offset = offset_saved
            if is_unicode:
                offset = cls.__stuff_unicode(buffer, offset, data, is_oref)
            else:
                offset = cls.__stuff_multibyte(buffer, offset, data, is_oref, locale)
        return offset

    @classmethod
    def __set_list_length_type(cls, buffer, offset, length, type):
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

    @classmethod
    def __get_pos_int_length(cls, data):
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

    @classmethod
    def __get_neg_int_length(cls, data):
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

    @classmethod
    def __stuff_raw_int(cls, buffer, offset, data, length):
        for i in range(length):
            one_byte = data & 255
            data = data >> 8
            buffer[offset+i] = one_byte
        return offset+length

    @classmethod
    def __stuff_empty_string(cls, buffer, offset):
        buffer[offset] = 3
        buffer[offset+1] = cls.ITEM_ASCII
        buffer[offset+2] = 0
        return offset+3

    @classmethod
    def __stuff_8bit_ascii(cls, buffer, offset, data, is_oref):
        try:
            list_type =  cls.ITEM_OREF_ASCII if is_oref else cls.ITEM_ASCII
            length = len(data)
            offset = cls.__set_list_length_type(buffer, offset, length, list_type)
            buffer[offset:offset+length] = data.encode("latin-1")
            return offset+length
        except Exception as e:
            return -1

    @classmethod
    def __stuff_unicode(cls, buffer, offset, data, is_oref):
        list_type =  cls.ITEM_OREF_UNICODE if is_oref else cls.ITEM_UNICODE
        byte_array = bytearray(data,"utf-16LE")
        length = len(byte_array)
        offset = cls.__set_list_length_type(buffer, offset, length, list_type)
        buffer[offset:offset+length] = byte_array[0:length]
        return offset+length

    @classmethod
    def __stuff_multibyte(cls, buffer, offset, data, is_oref, locale):
        list_type =  cls.ITEM_OREF_ASCII if is_oref else cls.ITEM_ASCII
        ascii = data.encode(locale)
        length = len(ascii)
        offset = cls.__set_list_length_type(buffer, offset, length, list_type)
        buffer[offset:offset+length] = ascii
        return offset + length

    @classmethod
    def __parse_decimal(cls, scale, num):
        decstr = str(num) + "E" + str(scale)
        dec = decimal.Decimal(decstr)
        return dec

    @classmethod
    def __get_bitlength(cls, value):
        if value < 0:
            return (value + 1).bit_length()
        else:
            return value.bit_length()

    @classmethod
    def _set_type_as_pass_by_reference(cls, buffer, offset):
        if buffer[offset] == 0:
            buffer[offset+3] = buffer[offset+3]+32
        elif buffer[offset] == 1:
            pass
        else:
            buffer[offset+1] = buffer[offset+1]+32
        return

_DBList._get_switcher = {
    _DBList.ITEM_ASCII: _DBList._grab_ascii_string,
    _DBList.ITEM_UNICODE: _DBList._grab_unicode_string,
    _DBList.ITEM_POSINT: _DBList._grab_pos_integer,
    _DBList.ITEM_NEGINT: _DBList._grab_neg_integer,
    _DBList.ITEM_POSNUM: _DBList._grab_pos_number,
    _DBList.ITEM_NEGNUM: _DBList._grab_neg_number,
    _DBList.ITEM_DOUBLE: _DBList._grab_double,
    _DBList.ITEM_COMPACT_DOUBLE: _DBList._grab_compact_double,
    _DBList.ITEM_OREF_ASCII: _DBList._grab_oref_ascii,
    _DBList.ITEM_OREF_UNICODE: _DBList._grab_oref_unicode
}

_DBList._set_switcher = {
    type(None): _DBList._stuff_null,
    bytes: _DBList._stuff_bytes,
    bytearray: _DBList._stuff_bytes,
    bool: _DBList._stuff_int,
    int: _DBList._stuff_int,
    float: _DBList._stuff_double,
    decimal.Decimal: _DBList._stuff_decimal,
    str: _DBList._stuff_str,
    _IRISOREF._IRISOREF: _DBList._stuff_str,
}
