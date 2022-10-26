# Module that covers the DollarList classes
# DollarListReader and DollarListWriter
# DollarItem is a class that is used by the DollarList classes
# to store the data in a list of objects
#

from dataclasses import dataclass, field
from enum import Enum
import struct
from typing import Any,List

class Dollartype(Enum):
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
    """
    A class that represents a dollar item
    """
    # type of the item
    dollar_type: Dollartype = Dollartype.ITEM_UNDEF
    # value of the item
    value: Any = None
    # raw data of the item
    raw_value: bytes = b''
    # raw data of the item + meta data
    buffer: bytes = b''
    # offset of the item in the list buffer
    offset: int = 0
    # length of the item in defined in the meta data
    meta_value_length: int = 0
    # length of the meta data
    meta_offset: int = 0

    def __str__(self) -> str:
        return f'{self.dollar_type} {self.value}'

# create DollarList exceptions
class DollarListException(Exception):
    """
    Base class for DollarList exceptions
    """

class DollarListReader:

    def __init__(self, buffer:bytes):
        self.items = []
        self.buffer = buffer
        self.offset = 0
        self.next_offset = 0
        self.read_buffer()

    def read_buffer(self):
        """
        read the buffer and return a list of DollarItems
        """
        while self.next_offset < len(self.buffer):
            item = self.get_next_item()
            self.items.append(item)

    def get_item_length(self,offset):
        """
        Get the length of the item in the meta data and the length of the meta data
        """
        meta_value_length = 0
        meta_offset = 0
        if self.buffer[offset] == 0:
            # case when length is in more than one byte
            i = 1
            while self.buffer[offset+i] == 0:
                # check how many bytes are used to store the length
                # by counting the number of 0 bytes
                i += 1
            # meta data length is the number of bytes used to store the length
            # plus the number of 0 bytes
            # plus the length itself
            # plus the type byte
            meta_offset = 2*i+2
            # cast the length to an integer
            meta_value_length = int.from_bytes(self.buffer[offset+i:offset+2*i+1],
                                                byteorder='little')
        elif self.buffer[offset] == 1:
            # case where data is null
            meta_value_length = 0
        else:
            # case where the length is first byte
            meta_value_length = self.buffer[offset]
            meta_offset += 2
        if meta_value_length > len(self.buffer) or meta_value_length <= 0:
            raise DollarListException("Invalid length")
        return meta_value_length, meta_offset

    def get_item_type(self,offset,meta_offset=None):
        if meta_offset is None:
            meta_offset = self.get_item_length(offset)[1]
        typ = self.buffer[offset+meta_offset-1]
            # if result is not between 0 and 9, then raise an exception
        if typ < 0 or typ > 9:
            raise DollarListException("Invalid type")
        return typ

    def get_item_raw_value(self,offset,meta_offset=None,length=None):
        if meta_offset is None or length is None:
            length, meta_offset = self.get_item_length(offset)
        return self.buffer[offset+meta_offset:offset+length]

    def get_item_buffer(self,offset,meta_offset=None,length=None):
        if meta_offset is None or length is None:
            length, meta_offset = self.get_item_length(offset)
        return self.buffer[offset:offset+length]

    def get_item_value(self,offset,meta_offset=None,length=None,typ=None,raw_value=None):
        val = None
        if meta_offset is None or length is None:
            length, meta_offset = self.get_item_length(offset)
        if typ is None:
            typ = self.get_item_type(
                    offset=offset,
                    meta_offset=meta_offset
                )
        if raw_value is None:
            raw_value = self.get_item_raw_value(offset,meta_offset,length)
        if typ == Dollartype.ITEM_ASCII.value:
            val = self.get_ascii(raw_value)
        elif typ == Dollartype.ITEM_UNICODE.value:
            val = raw_value.decode('utf-16')
        elif typ == Dollartype.ITEM_POSINT.value:
            val = self.get_posint(raw_value)
        elif typ == Dollartype.ITEM_NEGINT.value:
            val = self.get_negint(raw_value)
        elif typ == Dollartype.ITEM_POSNUM.value:
            val = self.get_posnum(raw_value)
        elif typ == Dollartype.ITEM_NEGNUM.value:
            val = struct.unpack('<q',raw_value)[0]
        elif typ == Dollartype.ITEM_DOUBLE.value:
            val = struct.unpack('<d',raw_value)[0]
        elif typ == Dollartype.ITEM_COMPACT_DOUBLE.value:
            val = struct.unpack('<f',raw_value)[0]
        else:
            val = None
        return val

    def get_ascii(self,raw_value):
        """
        Decode the value as ascii.
        If decoding fails, consider the value as a sub-list.
        If decoding the sub-list fails, consider the value as a binary.
        """
        if raw_value == b'':
            return None
        try:
            return DollarList.from_bytes(raw_value)
        except DollarListException:
            try:
                return raw_value.decode('ascii')
            except UnicodeDecodeError:
                return raw_value

    def get_posint(self,raw_value):
        return int.from_bytes(raw_value, "little")

    def get_negint(self,raw_value):
        return int.from_bytes(raw_value, "little",signed=True)

    def get_posnum(self,raw_value):
        # parse the bytes as a float
        # using IEEE 754 standard
        return struct.unpack('<d',raw_value)[0]

    def get_negnum(self,raw_value):
        return struct.unpack('<q',raw_value)[0]

    def get_item(self,offset) -> DollarItem:
        item = DollarItem()
        item.offset = offset
        item.meta_value_length,item.meta_offset = self.get_item_length(offset)
        item.dollar_type = self.get_item_type(
            offset=offset,
            meta_offset=item.meta_offset,
        )
        item.raw_value = self.get_item_raw_value(offset,item.meta_offset,item.meta_value_length)
        item.buffer = self.get_item_buffer(offset,item.meta_offset,item.meta_value_length)
        item.value = self.get_item_value(offset,item.meta_offset,item.meta_value_length)
        # if value is a list change the typ to ITEM_PLACEHOLDER
        if isinstance(item.value,DollarList):
            item.dollar_type = 0
        return item

    def get_next_item(self) -> DollarItem:
        item = self.get_item(self.next_offset)
        self.next_offset = self.get_next_offset(self.next_offset)
        return item

    def get_next_offset(self,offset):
        if self.buffer[offset] != 0:
            next_offset = offset + self.buffer[offset]
        elif self.buffer[offset + 1] == 0 and self.buffer[offset + 2] == 0:
            if offset + 6 < len(self.buffer):
                next_offset = (
                                self.buffer[offset + 3] |
                                (self.buffer[offset + 4] << 8) |
                                (self.buffer[offset + 5] << 16)
                              ) + 7
        elif offset + 2 < len(self.buffer):
            next_offset = (self.buffer[offset + 1] | (self.buffer[offset + 2] << 8)) + 3
        return next_offset

@dataclass
class DollarList:

    items: List[DollarItem] = field(default_factory=list)

    # add to the dataclass a new constructor from_bytes
    @staticmethod
    def from_bytes(buffer:bytes):
        cls = DollarList()
        cls.items = DollarListReader(buffer).items
        return cls

    def __str__(self):
        """
        Return a string representation of the list.
        Like the dollar list representation with $lb
        """
        return self._str_(self.items)

    @classmethod
    def _str_(cls,items):
        """
        Return a string representation of the list.
        Like the dollar list representation with $lb"""
        result = "$lb("
        for item in items:

            if item.dollar_type in (Dollartype.ITEM_ASCII.value,
                                    Dollartype.ITEM_UNICODE.value):
                if item.value is None:
                    result += '""' # way of iris to represent null string
                else:
                    result += f'"{item.value}"'

            elif item.dollar_type == Dollartype.ITEM_PLACEHOLDER.value:
                result += cls._str_(item.value.items)
            else:
                result += f'{item.value}'
            result += ","
        if len(items) > 0:
            result = result[:-1]
        result += ")"
        return result

    @classmethod
    def _to_list(cls,items):
        """
        Convert a list of DollarItems to a list of python objects
        """
        result = []
        for item in items:
            if item.dollar_type == 0:
                result.append(cls._to_list(item.value))
            else:
                result.append(item.value)
        return result

    def to_list(self):
        """
        Convert a list of DollarItems to a list of python objects
        """
        return self._to_list(self.items)

    # build iterator for values
    def __iter__(self):
        return iter(self.items)

if __name__ == '__main__':
        data = b'\x06\x01test\x05\x01\x03\x04\x04'
        reader = DollarList.from_bytes(data)
        value = [x.value for x in reader]
        print(value)