# ListBuildReader is a class that reads an IRIS ListBuild binary 
# and returns a python list of the items in the binary.
# items in the binary have the following format:
# N bytes: length of the item in bytes where N is the number of bytes
# N = 1 + number of bytes that are not 0x00
# 1 byte: type of the item
# M bytes: value of the item where M is the length of the item

import struct

class ListBuildReader:
    def __init__(self, binary):
        self.binary = binary
        self.index = 0
        self.result = []
        self.length = len(binary)
        self.read_list()

    def read_list(self):
        while self.index < self.length:
            self.read_item()
        return self.result

    def read_item(self):
        length = self.read_length()
        type = self.read_type()
        value = self.read_value(length)
        self.result.append(value)

    def read_length(self):
        length = 0
        while True:
            byte = self.read_byte()
            length = length + 1
            if byte != 0:
                break
        return length

    def read_type(self):
        return self.read_byte()

    def read_value(self, length):
        value = self.read_bytes(length)
        return value

    def read_byte(self):
        byte = self.binary[self.index]
        self.index = self.index + 1
        return byte

    def read_bytes(self, length):
        bytes = self.binary[self.index:self.index + length]
        self.index = self.index + length
        return bytes

class ListBuildIterator():
    # This class is a generator that reads an IRIS ListBuild binary
    # It makes use of the ListBuildReader class to read the binary

    def __init__(self, binary):
        self.binary = binary
        self.reader = ListBuildReader(binary)
        self.index = 0
        self.length = len(self.reader.result)

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < self.length:
            item = self.reader.result[self.index]
            self.index = self.index + 1
            return item
        else:
            raise StopIteration

