# dollarlist is a list of bytes chunks
# each chunk is an item
# each item as a length, a type, and a value

# DollarListParser is an iterator that help parse a dollarlist of bytes
# it returns a tuple of (length, type, value)
# lenght is an integer that represent the number of bytes of the item
# type is an integer that represent the type of the item
# value is the value of the item in bytes

from enum import Enum
from typing import Tuple


class DollarType(Enum):
    ITEM_UNDEF = -1
    ITEM_PLACEHOLDER = 0
    ITEM_ASCII = 1
    ITEM_UNICODE = 2
    ITEM_POSINT = 4
    ITEM_NEGINT = 5
    ITEM_POSNUM = 6
    ITEM_NEGNUM = 7
    ITEM_DOUBLE = 8
    ITEM_COMPACT_DOUBLE = 9

class DollarListParser:
    def __init__(self, buffer:bytes):
        # buffer is the dollarlist in bytes
        self.buffer = buffer
        # data is the current item in bytes
        self.data = None
        # data_offset is the offset of the current item in the buffer
        self.data_offset = 0
        # data_length is the length of the current item in the buffer
        self.data_length = 0
        # buffer_length is the length of the buffer item
        self.buffer_length = len(buffer)
        # offset is the offset of the current item in the buffer
        self.offset = 0
        # next_offset is the offset of the next item in the buffer
        self.next_offset = 0
        # length is the length of the current item
        self.length = len(buffer)
        # type is the type of the current item
        self.type = 0
        self.is_null = False
        self.is_undefined = False



    def __iter__(self):
        return self

    def __next__(self) -> Tuple[int, int, bytes]:
        if self.offset < self.length:
            self._get_next_offset()
            self.offset = self.next_offset

            return (self.length, self.type, self.data)
        else:
            raise StopIteration

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
    def _get_raw_data(cls, buffer, offset, next_offset):
        pass

    def _get_next_offset(self):
        buffer = self.buffer
        offset = self.next_offset
        # if first byte is 0, then length is next 2 bytes
        if buffer[offset] == 0:
            length = buffer[offset + 1] | (buffer[offset + 2] << 8);
            offset += 3
            # if the length is still 0, then the length is the next 4 bytes
            if length == 0:
                length = buffer[offset] | (buffer[offset + 1] << 8) | (buffer[offset + 2] << 16) | (buffer[offset + 3] << 24);
                offset += 4
            self.type = buffer[offset]
            if self.type >= 32 and self.type < 64:
                self.type = self.type-32
            self.data_offset = offset + 1
            self.data_length = length - 1
            self.next_offset = self.data_offset + self.data_length
            self.is_null = False
            self.is_undefined = False
        elif buffer[offset] == 1:
            self.type = DollarType.ITEM_UNDEF
            if self.type >= 32 and self.type < 64:
                self.type = self.type-32
            self.data_offset = offset + 1
            self.data_length = 0
            self.next_offset = self.data_offset
            self.is_null = True
            self.is_undefined = True
        else:
            self.type = buffer[offset + 1]
            if self.type >= 32 and self.type < 64:
                self.type = self.type-32
            self.data_offset = offset + 2
            self.data_length = buffer[offset] - 2
            self.next_offset = self.data_offset + self.data_length
            self.is_null = (self.type == DollarType.ITEM_PLACEHOLDER) or ((self.type == DollarType.ITEM_ASCII) and (self.data_length == 0))
            self.is_undefined = False
        return 

