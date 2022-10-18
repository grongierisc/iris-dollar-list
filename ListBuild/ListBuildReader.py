# ListBuildReader is a class that reads an IRIS ListBuild binary 
# and returns a python list of the items converted from there binary format.
# items in the binary have the following format:
# N bytes: length of the item in bytes where N is the number of bytes
# N = 1 + number of bytes that are not 0x00
# 1 byte: type of the item
# types are:
# bin value: meaning: python type
# 0x00: null: None
# 0x01: ascii: str
# to decode ascii to str, use the following:
# use a variable called encoding to store the encoding
# if decoding fails, use the following:
# consider the item as an sub-list
# if sub-list decoding fails, use the following:
# consider the item as a binary
# 0x02: unicode: str
# to decode unicode to str, use the following:
# decode the item as utf-16
# 0x04: positive integer: int
# 0x05: negative integer: int
# 0x06: positive float: float
# 0x07: negative float: float
# 0x08: double: float
# 0x09: compact double: float

# M bytes: value of the item where M is the length of the item

from enum import Enum
import struct

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

class ListBuildReader:
    def __init__(self, binary):
        self.binary = binary
        self.locale = 'latin-1'
        self.index = 0
        self.result = []
        self.length = len(binary)
        self.read_list()

    def read_list(self):
        while self.index < self.length:
            self.read_item()
        return self.result

    def read_item(self):
        """
        Read an item from the binary.
        The item has the following format:
        read the length of the item
        read the type of the item
        read the value of the item
        """
        length = self.read_length()
        type = self.read_type()
        value = self.read_value(length, type)
        self.result.append(value)

    def read_length(self):
        """
        Read the length of the item.
        The length is the number of bytes that the item takes up.
        The length is encoded in the following way:
        if the length is less than 256, the length is encoded in 1 byte
        if the length is greater than 256, the length is encoded in 1 byte + the number of bytes that are not 0x00
        first check how many bytes are 0x00
        then add 1 to the number of bytes that are not 0x00
        then read the length of the item
        """
        length = 0
        while self.read_bytes() == 0:
            pass
        length = length + 1
        return int.from_bytes(self.read_bytes(length,False), byteorder='big', signed=False)

    def read_type(self):
        """
        Read the type of the item.
        The type is encoded in 1 byte.
        Convert the byte to an integer.
        Make use of the DollarType enum.
        """
        return DollarType(int.from_bytes(self.read_bytes(), byteorder='big', signed=False)).value

    def read_bytes(self, length=1,increment=True):
        """
        Read a number of bytes from the binary.
        """
        bytes = self.binary[self.index:self.index + length]
        # increment the index if increment is True
        if increment:
            self.index = self.index + length
        return bytes

    def read_value(self, length, type):
        """
        Read the value of the item.
        The value is encoded in the following way:
        if the type is ITEM_ASCII, decode the value as ascii
        if the type is ITEM_UNICODE, decode the value as unicode
        if the type is ITEM_POSINT, decode the value as a positive integer
        if the type is ITEM_NEGINT, decode the value as a negative integer
        if the type is ITEM_POSNUM, decode the value as a positive float
        if the type is ITEM_NEGNUM, decode the value as a negative float
        if the type is ITEM_DOUBLE, decode the value as a double
        if the type is ITEM_COMPACT_DOUBLE, decode the value as a compact double
        """
        value = self.read_bytes(length)
        if type == DollarType.ITEM_ASCII.value:
            return self.decode_ascii(value)
        if type == DollarType.ITEM_UNICODE.value:
            return self.decode_unicode(value)
        if type == DollarType.ITEM_POSINT.value:
            return self.decode_positive_integer(value)
        if type == DollarType.ITEM_NEGINT.value:
            return self.decode_negative_integer(value)
        if type == DollarType.ITEM_POSNUM.value:
            return self.decode_positive_float(value)
        if type == DollarType.ITEM_NEGNUM.value:
            return self.decode_negative_float(value)
        if type == DollarType.ITEM_DOUBLE.value:
            return self.decode_double(value)
        if type == DollarType.ITEM_COMPACT_DOUBLE.value:
            return self.decode_compact_double(value)

    def decode_ascii(self, value):
        """
        Decode the value as ascii.
        If decoding fails, consider the value as a sub-list.
        If decoding the sub-list fails, consider the value as a binary.
        """
        try:
            return value.decode(self.locale)
        except:
            try:
                return self.decode_sub_list(value)
            except:
                return value

    def decode_unicode(self, value):
        """
        Decode the value as unicode.
        If decoding fails, consider the value as a binary.
        """
        try:
            return value.decode('utf-16')
        except:
            return value

    def decode_positive_integer(self, value):
        return int.from_bytes(value, byteorder='big', signed=False)

    def decode_negative_integer(self, value):
        return int.from_bytes(value, byteorder='big', signed=True)

    def decode_positive_float(self, value):
        return float.fromhex(value.hex())

    def decode_negative_float(self, value):
        return -float.fromhex(value.hex())

    def decode_double(self, value):
        return struct.unpack('>d', value)[0]

    def decode_compact_double(self, value):
        return struct.unpack('>d', value)[0]

    def decode_sub_list(self, value):
        return ListBuildReader(value).read_list()