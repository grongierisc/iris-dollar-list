import ListBuildReader

dollar_list_empty_list = b'\x01'
dollar_list_one_element = b'\x03\x01\x88' # one item : lenght 3, type ascii, value 136 'X'
dollar_list_two_elements = b'\x03\x01\x88\x03\x01\x89' # two items :
                                                       # item one : lenght 3, type ascii, value 136 'X'
                                                       # item tow : lenght 3, type ascii, 137 'Y'

result = ListBuildReader.ListBuildReader(b'\x03\x01X\x03\x04\x01\t\x01\x07\x01ttest')
print(result.result)