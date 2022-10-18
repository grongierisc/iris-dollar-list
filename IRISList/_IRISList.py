import _DBList
import _ListReader
import _ListWriter
import _IRIS

class _IRISList(object):
    '''
    This class provides an interface to interact with IRIS $LIST data.
'''

    def __init__(self, buffer = None, locale = "latin-1", is_unicode = True, compact_double = False):
        self._list_data = []
        self._locale = locale
        self._is_unicode = is_unicode
        self.compact_double = compact_double
        try:
            if buffer == None:
                return
            if type(buffer) == IRISList:
                buffer = buffer.getBuffer()
            if type(buffer) == bytes or type(buffer) == bytearray:
                list_reader = _ListReader._ListReader(buffer, locale)
                while not list_reader._is_end():
                    value = list_reader._get(True)
                    if value is None and list_reader.list_item.type !=  _DBList._DBList.ITEM_UNDEF:
                        value = bytes()
                    self._list_data.append(value)
                return
        except Exception as ex:
            raise ex
        raise Exception("data is not valid for IRISList format")

    def get(self, index):
        '''
Returns the value at a given index.

get(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns bytes, Decimal, float, int, str, or IRISList.
'''
        raw_data = self._list_data[index-1]
        if type(raw_data) == IRISList:
            raw_data = raw_data.getBuffer()
        if type(raw_data) == bytes:
            return _convertToString(raw_data, MODE_LIST, self._locale)
        return raw_data

    def getBoolean(self, index):
        '''
Returns the value at a given index as a boolean.

getBoolean(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns bool.
'''
        raw_data = self._list_data[index-1]
        if type(raw_data) == IRISList:
            raw_data = raw_data.getBuffer()
        return _convertToBoolean(raw_data, MODE_LIST, self._locale)

    def getBytes(self, index):
        '''
Returns the value at a given index as bytes.

getBytes(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns bytes.
'''
        raw_data = self._list_data[index-1]
        if type(raw_data) == IRISList:
            return raw_data.getBuffer()
        return _convertToBytes(raw_data, MODE_LIST, self._locale, self._is_unicode)

    def getDecimal(self, index):
        '''
Returns the value at a given index as a Decimal.

getDecimal(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns Decimal.
'''
        raw_data = self._list_data[index-1]
        if type(raw_data) == IRISList:
            raw_data = raw_data.getBuffer()
        return _convertToDecimal(raw_data, MODE_LIST, self._locale)

    def getFloat(self, index):
        '''
Returns the value at a given index as a float.

getFloat(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns float.
'''
        raw_data = self._list_data[index-1]
        if type(raw_data) == IRISList:
            raw_data = raw_data.getBuffer()
        return _convertToFloat(raw_data, MODE_LIST, self._locale)

    def getInteger(self, index):
        '''
Returns the value at a given index as an integer.

getInteger(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns int.
'''
        raw_data = self._list_data[index-1]
        if type(raw_data) == IRISList:
            raw_data = raw_data.getBuffer()
        return _convertToInteger(raw_data, MODE_LIST, self._locale)

    def getString(self, index):
        '''
Returns the value at a given index as a string.

getString(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns str.
'''
        raw_data = self._list_data[index-1]
        if type(raw_data) == IRISList:
            raw_data = raw_data.getBuffer()
        return _convertToString(raw_data, MODE_LIST, self._locale)

    def getIRISList(self, index):
        '''
Returns the value at a given index as an IRISList.

getBytes(index)

Parameters
----------
index : one-based index of the IRISList.

Return Value
------------
Returns IRISList.
'''
        raw_data = self._list_data[index-1]
        if type(raw_data) == IRISList or raw_data == None:
            return raw_data
        return IRISList(_convertToBytes(raw_data, MODE_LIST, self._locale, self._is_unicode), self._locale, self._is_unicode, self.compact_double)

    def add(self, value):
        '''
Adds a data element at the end of the IRISList.

add(value)

Parameters
----------
value : value of the data to be added.

Return Value
------------
Returns the current IRISList object.
'''
        self._list_data.append(self._convertToInternal(value))
        return self

    def set(self, index, value):
        '''
Change data element at a given index location. If the index is beyond the length of the IRISList, IRISList will be first expanded to that many elements, paded with None elements.

set(index, value)

Parameters
----------
index: index at which the data is set to. index is one-based.
value : value of the data to be added.

Return Value
------------
Returns the current IRISList object.
'''
        if index>len(self._list_data):
            self._list_data.extend([None]*(index-len(self._list_data)))
        self._list_data[index-1] = self._convertToInternal(value)
        return self

    def _convertToInternal(self, value):
        if type(value) == bytearray:
            return bytes(value)
        if type(value) == IRISList:
            if not self.compact_double and value.compact_double:
                raise ValueError("Cannot embed an IRISList with Compact Double enabled into an IRISList with Compact Double disabled")
            return IRISList(value.getBuffer(), value._locale, value._is_unicode, value.compact_double)
        return value

    def remove(self, index):
        '''
Remove a data element at a given index location.

remove(index, value)

Parameters
----------
index: index at which the data is to be removed. index is one-based.

Return Value
------------
Returns the current IRISList object.
'''
        del self._list_data[index-1]
        return self

    def size(self):
        '''
Return the length of the data buffer

size()

Return Value
------------
Returns int.
'''
        return len(self.getBuffer())

    def count(self):
        '''
Return the unmber of data elements in the IRISList.

count()

Return Value
------------
Returns int.
'''
        return len(self._list_data)

    def clear(self):
        '''
Clears out all data in the IRISList.

clear()

Return Value
------------
Returns the current IRISList object.
'''
        self._list_data = []
        return self

    def equals(self, irislist2):
        '''
Returns a boolean indicate if the IRISList is the same as the IRISList of the argument

equals(irislist2)

Parameters
----------
irislist2: the second IRISList object to which to compare.

Return Value
------------
Returns bool.
'''
        if type(irislist2) != IRISList:
            raise TypeError("Argument must be an instance of IRISList")
        if len(self._list_data) != len(irislist2._list_data):
            return False
        for i in range(len(self._list_data)):
            if self.get(i+1) != irislist2.get(i+1):
                return False
        return True

    def __str__(self):
        display = ""
        for i in range(len(self._list_data)):
            raw_data = self._list_data[i]
            if type(raw_data) == IRISList:
                raw_data = raw_data.__str__()
            elif type(raw_data) == bool:
                raw_data = 1 if raw_data else 0
            if type(raw_data) == bytes:
                try:
                    if len(raw_data) == 0:
                        one_value = "empty"
                    else:
                        one_value = IRISList(raw_data).__str__()
                except Exception:
                    one_value = str(raw_data)
            elif type(raw_data) == str:
                try:
                    if len(raw_data) == 0:
                        one_value = "empty"
                    else:
                        one_value = IRISList(bytes(raw_data,"latin-1")).__str__()
                except Exception:
                    one_value = str(raw_data)
            else:
                one_value = str(raw_data)
            display += one_value + ","
        return "$lb(" + display[0:-1] + ")"

    def getBuffer(self):
        '''
Returns a byte array that contains the $LIST format of all the data elements.

getBuffer()

Return Value
------------
Returns bytes.
'''
        list_writer = _ListWriter._ListWriter(self._locale, self._is_unicode, self.compact_double)
        for i in range(len(self._list_data)):
            if self._list_data[i] == None:
                list_writer._set_undefined()
            elif type(self._list_data[i]) == IRISList:
                buffer = self._list_data[i].getBuffer()
                list_writer._set(buffer)
            else:
                list_writer._set(self._list_data[i], True)
        return bytes(list_writer._get_buffer())
