import Item

class _ListReader(object):

    def __init__(self, bufferarray:bytearray, locale="latin-1"):
        self.buffer = bufferarray
        self.list_item = Item._ListItem(bufferarray)
        self._locale = locale

    def __iter__(self):
        return self

    def __next__(self):
        if self._is_end():
            raise StopIteration
        else:
            return self._get(self.list_item,self._locale)

    def _get(self, as_bytes = False, retain_ascii_zero = False):
        self.list_item = self._get_list_element(self.list_item)
        if self.list_item.is_null:
            return None
        func = self._get_switcher.get(self.list_item.type, None)
        if func is None:
            raise Exception("Incorrect list format, unknown type: " + self.list_item.type)
        else:
            return func(self,self.list_item.buffer, self.list_item.data_offset, self.list_item.data_length, self._locale, as_bytes, retain_ascii_zero)


    def _get_raw_bytes(self, length):
        self.list_item.type = Item.DollarType.ITEM_PLACEHOLDER
        self.list_item.data_offset = 0
        self.list_item.data_length = 0
        self.list_item.next_offset = self.list_item.next_offset + length
        return self.list_item.buffer[self.list_item.next_offset - length:self.list_item.next_offset]

    def _is_end(self):
        return (self.list_item.next_offset >= self.list_item.list_buffer_end)

    def _get_at_offset(self, offset, as_bytes = False):
        self.list_item.next_offset = offset
        return self._get(as_bytes)

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
        return (self.list_item.type == Item.DollarType.ITEM_UNDEF)

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

    def _get_list_element(self, item:Item._ListItem):
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
            item.type = Item.DollarType.ITEM_UNDEF
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
            item.is_null = (item.type == Item.DollarType.ITEM_PLACEHOLDER) or ((item.type == Item.DollarType.ITEM_ASCII) and (item.data_length == 0))
            item.is_undefined = False
        return item

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

    def __parse_decimal(self, scale, num):
        decstr = str(num) + "E" + str(scale)
        dec = decimal.Decimal(decstr)
        return dec

    def _grab_double(self, buffer, offset, length, *args):
        if length != 8: return self.__grab_compact_float(buffer, offset, length)
        return struct.unpack('d', buffer[offset:offset+length])[0]

    def _grab_compact_double(self, buffer, offset, length, *args):
        return struct.unpack('d',b'\x00\x00\x00\x00\x00\x00\x00\x00'[length:]+buffer[offset:offset+length])[0]

    def __grab_compact_float(self, buffer, offset, length):
        return struct.unpack('f',b'\x00\x00\x00\x00'[length:]+buffer[offset:offset+length])[0]

    _get_switcher = {
        Item.DollarType.ITEM_ASCII: _grab_ascii_string,
        Item.DollarType.ITEM_UNICODE: _grab_unicode_string,
        Item.DollarType.ITEM_POSINT: _grab_pos_integer,
        Item.DollarType.ITEM_NEGINT: _grab_neg_integer,
        Item.DollarType.ITEM_POSNUM: _grab_pos_number,
        Item.DollarType.ITEM_NEGNUM: _grab_neg_number,
        Item.DollarType.ITEM_DOUBLE: _grab_double,
        Item.DollarType.ITEM_COMPACT_DOUBLE: _grab_compact_double
    }