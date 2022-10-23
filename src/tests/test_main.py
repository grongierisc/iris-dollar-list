# Licensed under the MIT License
# https://github.com/grongierisc/dollar-list/blob/main/LICENSE

import unittest

from iris_dollar_list import DollarListReader

class TestDollarListReaderGetItemLengh(unittest.TestCase):

    def test_one_item(self):
        data = b'\x03\x01t'
        reader = DollarListReader(b'')
        reader.buffer = data
        length,meta_offset = reader.get_item_length(0)
        self.assertEqual(length,3)
        self.assertEqual(meta_offset,2)

    def test_two_items(self):
        data = b'\x03\x01t\x03\x01t'
        reader = DollarListReader(b'')
        reader.buffer = data
        length,meta_offset = reader.get_item_length(0)
        self.assertEqual(length,3)
        self.assertEqual(meta_offset,2)
        length,meta_offset = reader.get_item_length(3)
        self.assertEqual(length,3)
        self.assertEqual(meta_offset,2)

    def test_one_item_length_0(self):
        data = b'\x02\x01'
        reader = DollarListReader(b'')
        reader.buffer = data
        length,meta_offset = reader.get_item_length(0)
        self.assertEqual(length,2)
        self.assertEqual(meta_offset,2)

    def test_long_length(self):
        # build a list with a long length
        # payload is A*256
        payload = b'\x41'*256
        data = b'\x00\x01\x01\x01' + payload
        reader = DollarListReader(b'')
        reader.buffer = data
        length,meta_offset = reader.get_item_length(0)
        self.assertEqual(length,257)
        self.assertEqual(meta_offset,4)
    
    def test_long_long_length(self):
        # build a list with a long length
        # payload is A*256*256
        payload = b'\x41'*256*256
        data = b'\x00\x00\x00\x01\x00\x01\x00\x01' + payload
        reader = DollarListReader(b'')
        reader.buffer = data
        length,meta_offset = reader.get_item_length(0)
        self.assertEqual(length,65537)
        self.assertEqual(meta_offset,8)

class TestDollarListReaderGetItemType(unittest.TestCase):

    def test_ascii_type(self):
        data = b'\x03\x01t'
        reader = DollarListReader(b'')
        reader.buffer = data
        item_type = reader.get_item_type(0)
        self.assertEqual(item_type,1)
        item_value = reader.get_item_value(0)
        self.assertEqual(item_value,'t')

    def test_unicode_type(self):
        data = b'\x04\x026\x05'
        reader = DollarListReader(b'')
        reader.buffer = data
        item_type = reader.get_item_type(0)
        self.assertEqual(item_type,2)
        item_value = reader.get_item_value(0)
        self.assertEqual(item_value,'Զ')

    def test_positive_integer_type(self):
        data = b'\x03\x04\x01'
        reader = DollarListReader(b'')
        reader.buffer = data
        item_type = reader.get_item_type(0)
        self.assertEqual(item_type,4)
        item_value = reader.get_item_value(0)
        self.assertEqual(item_value,1)
 
    def test_negative_integer_type(self):
        data = b'\x03\x05\xfe'
        reader = DollarListReader(b'')
        reader.buffer = data
        item_type = reader.get_item_type(0)
        self.assertEqual(item_type,5)
        item_value = reader.get_item_value(0)
        self.assertEqual(item_value,-2)

    def test_positive_float_type(self):
        # data = b'\x04\x06\xfee'
        # reader = DollarListReader(b'')
        # reader.buffer = data
        # item_type = reader.get_item_type(0)
        # self.assertEqual(item_type,6)
        # item_value = reader.get_item_value(0)
        # self.assertEqual(item_value,1.01)
        pass

    def test_negative_float_type(self):
        pass
    
    def test_double_type(self):
        pass

    def test_compact_double_type(self):
        pass

if __name__ == '__main__':
    # init the data
    unittest.main()


