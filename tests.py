import unittest
from DollarList import DollarListReader

class TestDollarListReaderGetItemLengh(unittest.TestCase):

    def test_one_item(self):
        data = b'\x03\x01t'
        reader = DollarListReader(data)
        length,meta_offset = reader.get_item_length(0)
        self.assertEqual(length,3)
        self.assertEqual(meta_offset,2)

    def test_two_items(self):
        data = b'\x03\x01t\x03\x01t'
        reader = DollarListReader(data)
        length,meta_offset = reader.get_item_length(0)
        self.assertEqual(length,3)
        self.assertEqual(meta_offset,2)
        length,meta_offset = reader.get_item_length(3)
        self.assertEqual(length,3)
        self.assertEqual(meta_offset,2)

    def test_one_item_length_0(self):
        data = b'\x02\x01'
        reader = DollarListReader(data)
        length,meta_offset = reader.get_item_length(0)
        self.assertEqual(length,2)
        self.assertEqual(meta_offset,2)

    def test_long_length(self):
        # build a list with a long length
        # payload is A*256
        payload = b'\x41'*256
        data = b'\x00\x01\x01\x01' + payload
        reader = DollarListReader(data)
        length,meta_offset = reader.get_item_length(0)
        self.assertEqual(length,257)
        self.assertEqual(meta_offset,4)
    
    def test_long_long_length(self):
        # build a list with a long length
        # payload is A*256*256
        payload = b'\x41'*256*256
        data = b'\x00\x00\x00\x01\x00\x01\x00\x01' + payload
        reader = DollarListReader(data)
        length,meta_offset = reader.get_item_length(0)
        self.assertEqual(length,65537)
        self.assertEqual(meta_offset,8)


if __name__ == '__main__':
    # init the data
    unittest.main()

