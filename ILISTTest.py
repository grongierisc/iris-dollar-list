import IList

dollar_list_one_element = b'\x03\x01\x88' # one item : lenght 3, type ascii, value 136 'X'

for item in IList.DollarListParser(dollar_list_one_element):
    print(item)