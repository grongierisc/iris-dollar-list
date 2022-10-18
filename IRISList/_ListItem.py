import _DBList

class _ListItem(object):

    def __init__(self, buffer):
        self.buffer = buffer
        self.list_buffer_end = len(buffer)
        self.is_null = False
        self.type = _DBList._DBList.ITEM_PLACEHOLDER
        self.data_offset = 0
        self.data_length = 0
        self.next_offset = 0



