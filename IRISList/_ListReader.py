import _DBList
import _ListItem


class _ListReader(object):

    def __init__(self, bufferarray, locale="latin-1"):
        self.list_item = _ListItem._ListItem(bufferarray)
        self._locale = locale

    def __iter__(self):
        return self

    def __next__(self):
        if self._is_end():
            raise StopIteration
        else:
            return self._get()

    def _get(self, asBytes=False, retainAsciiZero=False):
        _DBList._DBList._get_list_element(self.list_item)
        return _DBList._DBList._get(self.list_item, self._locale, asBytes, retainAsciiZero)

    def get_inner_list(self):
        ba = self._get(True)
        if not ba:
            return None
        return _ListReader(ba, self._locale)

    def _get_raw_bytes(self, length):
        self.is_null = False
        self.list_item.type = _DBList._DBList.ITEM_PLACEHOLDER
        self.list_item.data_offset = 0
        self.list_item.data_length = 0
        self.list_item.next_offset = self.list_item.next_offset + length
        return self.list_item.buffer[self.list_item.next_offset - length:self.list_item.next_offset]

    def _is_end(self):
        return (self.list_item.next_offset >= self.list_item.list_buffer_end)
        
    def _get_at_offset(self, offset, asBytes = False):
        self.list_item.next_offset = offset
        _DBList._DBList._get_list_element(self.list_item)
        return _DBList._DBList._get(self.list_item, self._locale, asBytes)

    def _move_to_end(self):
        self.list_item.next_offset = self.list_item.list_buffer_end 

    def _get_offset(self):
        return self.list_item.next_offset

    def _next(self):
        return _DBList._DBList._get_list_element(self.list_item)

    def _get_output_parameter_list(self, begin, add_null):
        len = self.list_item.next_offset - begin
        offset = 3 if add_null else 0
        ba = bytearray(len + offset)
        if add_null:
            quote_quote = bytearray([3, 1, 0])
            ba = quote_quote
        ba[offset:len] = self.list_item.buffer[begin:len]
        return _ListReader._ListReader(ba, self._locale)

    def _is_past_last_item(self):
        return (self.list_item.data_offset >= self.list_item.list_buffer_end)

    def _is_undefined(self):
        return (self.list_item.type == _DBList._DBList.ITEM_UNDEF)

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
