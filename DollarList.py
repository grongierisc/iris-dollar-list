# DollarList is a List of DollarItems
# DollarWriter helps to convert python value to the binary representation
# DollarReader helps to convert binary representation to python value

# Dol

# disable pylint all warnings
# pylint: disable=all

from dataclasses import dataclass
from typing import List, Any, TypeVar, Generic, Type, Union, Optional, Tuple, Dict, Callable
from enum import Enum
from io import BytesIO
from struct import pack, unpack

T = TypeVar('T')

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
class DollarItem(Generic[T]):
    type: DollarType
    value: T
    data: bytes

class DollarList:
    def __init__(self, buffer:bytes):
        self.buffer = buffer
        self.offset = 0
        self.length = len(buffer)
        self.item = DollarItem(DollarType.ITEM_UNDEF, None, b'')

    def get_item(self) -> DollarItem:
        if self.offset < self.length:
            self.item = _get_list_element(self, self.item)
        return self.item

    def get_next_item(self) -> DollarItem:
        self.offset = self.item.next_offset
        return self.get_item()

    def get_next_item_value(self) -> Any:
        self.offset = self.item.next_offset
        self.item = _get_list_element(self, self.item)
        return self.item.value

    def get_next_item_type(self) -> DollarType:
        self.offset = self.item.next_offset
        self.item = _get_list_element(self, self.item)
        return self.item.type

    def get_next_item_data(self) -> bytes:
        self.offset = self.item.next_offset
        self.item = _get_list_element(self, self.item)
        return self.item.data

    def get_next_item_is_null(self) -> bool:
        self.offset = self.item.next_offset
        self.item = _get_list_element(self, self.item)
        return self.item.is_null

    def get_next_item_is_undefined(self) -> bool:
        self.offset = self.item.next_offset
        self.item = _get_list_element(self, self.item)
        return self.item.is_undefined

    def get_next_item_is_string(self) -> bool:
        self.offset = self.item.next_offset
        self.item = _get_list_element(self, self.item)
        return self.item.type == DollarType.ITEM_ASCII or self.item.type == DollarType.ITEM_UNICODE

    def get_next_item_is_number(self) -> bool:
        self.offset = self.item.next_offset
        self.item = _get_list_element(self, self.item)
        return self.item.type == DollarType.ITEM_POSINT or self.item.type == DollarType.ITEM_NEGINT or self.item.type == DollarType.ITEM_POSNUM or self.item.type == DollarType.ITEM_NEGNUM or self.item.type == DollarType.ITEM_DOUBLE or self.item.type == DollarType.ITEM_COMPACT_DOUBLE

    def get_next_item_is_int(self) -> bool:
        self.offset = self.item.next_offset
        self.item = _get_list_element(self, self.item)
        return self


class DollarReader:
    #DollarReader is a helper class to read a binary representation of a DollarList and convert it to a python list
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

def _get_list_element(self, item:DollarItem):
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
        return item


    


