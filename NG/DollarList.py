# Module that covers the DollarList classes
# DollarListReader and DollarListWriter
# DollarItem is a class that is used by the DollarList classes
# to store the data in a list of objects
#

from dataclasses import dataclass
from enum import Enum
import struct
from typing import Any

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

@dataclass
class DollarItem:
    type: DollarType = DollarType.ITEM_UNDEF
    value: Any = None
    raw_value: bytes = b''
    buffer: bytes = b''
    offset: int = 0
    length: int = 0
    length_offset: int = 0

class DollarList:
    def __init__(self, buffer:bytes):
        self.buffer = buffer
        self.offset = 0
        self.next_offset = 0
        self.length = len(buffer)
        self.items = []
        self.read_buffer()

    def read_buffer(self):
        """
        read the buffer and return a list of DollarItems
        """
        while self.next_offset < self.length:
            item = self.get_next_item()
            self.items.append(item)
    
    def get_item_length(self,offset):
        """
        get the length of the item at the given offset
        return the length and the offset of the length
        """
        length = 0
        if self.buffer[offset] == 0:
            # if first byte is 0, then length is next 2 bytes
            length = self.buffer[offset + 1] | (self.buffer[offset + 2] << 8);
            offset += 3
            # if the length is still 0, then the length is the next 4 bytes
            if length == 0:
                length = self.buffer[offset] | (self.buffer[offset + 1] << 8) | (self.buffer[offset + 2] << 16) | (self.buffer[offset + 3] << 24);
                offset += 4
        elif self.buffer[offset] == 1:
            # case where data is null
            length = 0
        else:
            # case where the length is first byte
            length = self.buffer[offset]
            offset += 1
        return length, offset

    def get_item_type(self,offset,length_offset=None,length=None):
        if length_offset is None:
            length, length_offset = self.get_item_length(offset)
        return self.buffer[length_offset]

    def get_item_raw_value(self,offset,length_offset=None,length=None):
        if length_offset is None or length is None:
            length, length_offset = self.get_item_length(offset)
        return self.buffer[length_offset+1:offset+length]

    def get_item_buffer(self,offset,length_offset=None,length=None):
        if length_offset is None or length is None:
            length, length_offset = self.get_item_length(offset)
        return self.buffer[offset:offset+length]

    def get_item(self,offset) -> DollarItem:
        item = DollarItem()
        item.offset = offset
        item.length,item.length_offset = self.get_item_length(offset)
        item.type = self.get_item_type(offset)
        item.raw_value = self.get_item_raw_value(offset)
        item.buffer = self.get_item_buffer(offset)
        return item

    def get_next_item(self) -> DollarItem:
        item = self.get_item(self.next_offset)
        self.next_offset = item.offset + item.length
        return item

if __name__ == '__main__':
    result = DollarList(b'\x03\x01X\x03\x04\x01\t\x01\x07\x01ttest')
    print(result)