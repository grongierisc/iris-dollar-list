import DollarList

dollar_list_one_element = b'\x01\x01\x88' # one item : lenght 3, type ascii, value 136 'X'

dl = DollarList.DollarList.from_bytes(dollar_list_one_element)
print(dl)