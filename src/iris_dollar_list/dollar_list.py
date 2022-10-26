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

class DollarListWriter:
    """
    Convert a DollarList to it's byte form
    """
    def __init__(self,dollar_list):
        self.dollar_list = dollar_list
        self.buffer = b''
        self.offset = 0

    def create_dollar_item(self,item):
        """
        Create a DollarItem from a python object
        Based on the item type convert it
        """
        if isinstance(item,DollarItem):
            return item
        elif isinstance(item,DollarList):
            return DollarItem(value=item)
        elif isinstance(item,str):
            return self.create_from_string(item)
        elif isinstance(item,int):
            return self.create_from_int(item)
        elif isinstance(item,float):
            raise DollarListException("Floats are not supported")
        elif isinstance(item,bytes):
            raise DollarListException("Bytes are not supported")
        else:
            raise DollarListException("Invalid item type")

    def create_from_string(self,item):
        """
        Create a DollarItem from a string
        """
        result = DollarItem()
        if item == '':
            result = self.create_null_item()
        try:
            result = self.create_from_ascii(item,'ascii')
        except UnicodeEncodeError:
            try:
                result = self.create_from_ascii(item,'latin-1')
            except UnicodeEncodeError:
                result = self.create_from_ascii(item,'utf-16')
        return result

    def create_null_item(self):
        """
        Create a DollarItem with a null value
        """
        raw_value = b''
        value = None
        lenght = b'\x02'
        buffer = lenght + Dollartype.ITEM_ASCII.value.to_bytes(1, "little") + raw_value
        return DollarItem(
            value=value,
            raw_value=raw_value,
            buffer=buffer,
            dollar_type=Dollartype.ITEM_ASCII.value,
        )

    def create_from_ascii(self,item,locale):
        """
        Create a DollarItem from a string
        """
        raw_value = value=item.encode(locale)
        value = item
        lenght = self.get_meta_value_length(raw_value)
        if locale != 'utf-16':
            typ = Dollartype.ITEM_ASCII.value
        else:
            typ = Dollartype.ITEM_UNICODE.value
        buffer = lenght + typ.to_bytes(1, "little") + raw_value
        return DollarItem(
            value=value,
            raw_value=raw_value,
            buffer=buffer,
            dollar_type=Dollartype.ITEM_ASCII.value,
        )

    def create_from_int(self,item):
        """
        Create a DollarItem from an integer
        """
        if item < 0:
            return self.create_negint(item)
        else:
            return self.create_posint(item)

    def create_negint(self,item):
        """
        Create a DollarItem from a negative integer
        """
        raw_value = item.to_bytes(item.bit_length(), "little",signed=True)
        value = item
        lenght = self.get_meta_value_length(raw_value)
        buffer = lenght + Dollartype.ITEM_NEGINT.value.to_bytes(1, "little") + raw_value
        return DollarItem(
            dollar_type=Dollartype.ITEM_NEGINT.value,
            value=value,
            raw_value=raw_value,
            buffer=buffer
        )

    def create_posint(self,item):
        """
        Create a DollarItem from a positive integer
        """
        raw_value = item.to_bytes(item.bit_length(), "little")
        value = item
        lenght = self.get_meta_value_length(raw_value)
        buffer = lenght + Dollartype.ITEM_POSINT.value.to_bytes(1, "little") + raw_value
        return DollarItem(
            dollar_type=Dollartype.ITEM_POSINT.value,
            value=value,
            raw_value=raw_value,
            buffer=buffer
        )

    def get_meta_value_length(self,raw_value):
        """
        Get the length of the raw value
        """
        result = b''
        length = len(raw_value) + 2 # add 2 for the type and length bytes
        # convert bit_length to bytes
        bytes_length = (length + 7) // 8
        # zero_prefix is the number of \x00 bytes that need to be added to the length
        length = len(raw_value) + 1 + bytes_length # add the type and length bytes
        for x in range(bytes_length):
            result += b'\x00' * x + (length).to_bytes(bytes_length, "little")

        return result


@dataclass
class DollarList:

    items: List[DollarItem] = field(default_factory=list)

    def to_bytes(self):
        """
        Convert a DollarList to bytes
        """
        buffer = b''
        for item in self.items:
            buffer += item.buffer
        return buffer

    @staticmethod
    def from_list(python_list):
        """
        Create a DollarListWriter from a python list
        For each item in the list, create a DollarItem
        """
        dollar_list = DollarList()
        dlw = DollarListWriter(dollar_list)
        for item in python_list:
            dollar_list.items.append(dlw.create_dollar_item(item))
        return dollar_list

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
    my_list = [1,-2,'3,4,5,6,7,8,9,10']
    dollar_list = DollarList.from_list(my_list)
    print(dollar_list.to_bytes())

        # data = b'\x06\x01test\x05\x01\x03\x04\x04'
        # reader = DollarList.from_bytes(data)
        # print(reader)
        # bytes = reader.to_bytes()
        # print(bytes)