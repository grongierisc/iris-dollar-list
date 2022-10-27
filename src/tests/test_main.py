# Licensed under the MIT License
# https://github.com/grongierisc/dollar-list/blob/main/LICENSE

import unittest

from iris_dollar_list import DollarList
from src.iris_dollar_list.dollar_list import DollarListReader

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
        # payload is A*255
        payload = b'\x41'*255
        data = b'\x00\x00\x01\x01' + payload
        reader = DollarListReader(data)
        length,meta_offset = reader.get_item_length(0)
        self.assertEqual(length,256)
        self.assertEqual(meta_offset,4)

    def test_long_long_length(self):
        # build a list with a long length
        # payload is A*256*256
        payload = b'\x41'*256*500
        data = b'\x00\x00\x00\x01\xf4\x01\x00\x01' + payload
        reader = DollarListReader(data)
        length,meta_offset = reader.get_item_length(0)
        self.assertEqual(length,128001)
        self.assertEqual(meta_offset,8)

class TestDollarListReaderGetItemType(unittest.TestCase):

    def test_ascii_type(self):
        data = b'\x03\x01t'
        reader = DollarListReader(data)
        item_type = reader.get_item_type(0)
        self.assertEqual(item_type,1)
        item_value = reader.get_item_value(0)
        self.assertEqual(item_value,'t')

    def test_unicode_type(self):
        data = b'\x04\x026\x05'
        reader = DollarListReader(data)
        item_type = reader.get_item_type(0)
        self.assertEqual(item_type,2)
        item_value = reader.get_item_value(0)
        self.assertEqual(item_value,'Զ')

    def test_positive_integer_type(self):
        data = b'\x03\x04\x01'
        reader = DollarListReader(data)
        item_type = reader.get_item_type(0)
        self.assertEqual(item_type,4)
        item_value = reader.get_item_value(0)
        self.assertEqual(item_value,1)

    def test_negative_integer_type(self):
        data = b'\x03\x05\xfe'
        reader = DollarListReader(data)
        item_type = reader.get_item_type(0)
        self.assertEqual(item_type,5)
        item_value = reader.get_item_value(0)
        self.assertEqual(item_value,-2)

    def test_positive_float_type(self):
        pass

    def test_negative_float_type(self):
        pass

    def test_double_type(self):
        pass

    def test_compact_double_type(self):
        pass

class TestDollarWriter(unittest.TestCase):
    
        def test_write_ascii(self):
            dl = DollarList()
            dl.append('t')
            self.assertEqual(dl.to_bytes(),b'\x03\x01t')
    
        def test_write_unicode(self):
            dl = DollarList()
            dl.append('Զ')
            self.assertEqual(dl.to_bytes(),b'\x06\x02\xff\xfe6\x05')
    
        def test_write_positive_integer(self):
            dl = DollarList()
            dl.append(1)
            self.assertEqual(dl.to_bytes(),b'\x03\x04\x01')
    
        def test_write_negative_integer(self):
            dl = DollarList()
            dl.append(-2)
            self.assertEqual(dl.to_bytes(),b'\x03\x05\xfe')

        def test_write_two_items(self):
            dl = DollarList()
            dl.append('t')
            dl.append('t')
            self.assertEqual(dl.to_bytes(),b'\x03\x01t\x03\x01t')

        def test_write_long_length(self):
            dl = DollarList()
            dl.append('A'*255)
            self.assertEqual(dl.to_bytes(),b'\x00\x00\x01\x01' + b'\x41'*255)

        def test_write_long_long_length(self):
            dl = DollarList()
            dl.append('A'*256*500)
            self.assertEqual(dl.to_bytes(),b'\x00\x00\x00\x01\xf4\x01\x00\x01' + b'\x41'*256*500)

        def test_write_null(self):
            dl = DollarList()
            dl.append(None)
            self.assertEqual(dl.to_bytes(),b'\x02\x01')

        def test_write_positive_float(self):
            pass
    
        def test_write_negative_float(self):
            pass
    
        def test_write_double(self):
            pass
    
        def test_write_compact_double(self):
            pass

class TestDollarList(unittest.TestCase):

    ## to string
    def test_to_string_empty(self):
        data = b'\x02\x01'
        reader = DollarList.from_bytes(data)
        value = str(reader)
        self.assertEqual(value,'$lb("")')

    def test_to_string_one_element(self):
        data = b'\x03\x01t'
        reader = DollarList.from_bytes(data)
        value = str(reader)
        self.assertEqual(value,'$lb("t")')

    def test_to_string_two_elements(self):
        data = b'\x03\x01t\x03\x04\x03'
        reader = DollarList.from_bytes(data)
        value = str(reader)
        self.assertEqual(value,'$lb("t",3)')

    def test_to_string_embedded_list(self):
        data = b'\x06\x01test\x05\x01\x03\x04\x04'
        reader = DollarList.from_bytes(data)
        value = str(reader)
        self.assertEqual(value,'$lb("test",$lb(4))')

    ## iterator
    def test_iterate_empty(self):
        data = b'\x02\x01'
        reader = DollarList.from_bytes(data)
        value = [x.value for x in reader]
        self.assertEqual(value,[None])

    def test_iterate_one_item(self):
        data = b'\x03\x01t'
        reader = DollarList.from_bytes(data)
        value = [x.value for x in reader]
        self.assertEqual(value,['t'])

    def test_iterate_two_items(self):
        data =  b'\x03\x01t\x03\x04\x03'
        reader = DollarList.from_bytes(data)
        value = [x.value for x in reader]
        self.assertEqual(value,['t',3])

    def test_iterate_embedded_list(self):
        data = b'\x06\x01test\x05\x01\x03\x04\x04'
        reader = DollarList.from_bytes(data)
        value = [x.value for x in reader]
        self.assertEqual(value[0],'test')
        self.assertTrue(isinstance(value[1],DollarList))

    ## to list
    def test_to_list_empty(self):
        data = b'\x02\x01'
        reader = DollarList.from_bytes(data)
        value = reader.to_list()
        self.assertEqual(value,[None])

    def test_to_list_one_item(self):
        data = b'\x03\x01t'
        reader = DollarList.from_bytes(data)
        value = reader.to_list()
        self.assertEqual(value,['t'])

    def test_to_list_two_items(self):
        data =  b'\x03\x01t\x03\x04\x03'
        reader = DollarList.from_bytes(data)
        value = reader.to_list()
        self.assertEqual(value,['t',3])

    def test_to_list_embedded_list(self):
        data = b'\x06\x01test\x05\x01\x03\x04\x04'
        reader = DollarList.from_bytes(data)
        value = reader.to_list()
        self.assertEqual(value[0],'test')
        self.assertTrue(isinstance(value[1],list))

    ## from list
    def test_from_list_empty(self):
        dl = DollarList.from_list([])
        self.assertEqual(dl.to_bytes(),b'\x02\x01')

    def test_from_list_one_item(self):
        dl = DollarList.from_list(['t'])
        self.assertEqual(dl.to_bytes(),b'\x03\x01t')


if __name__ == '__main__':
    # init the data
    unittest.main()
