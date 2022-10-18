from dataclasses import dataclass
from enum import Enum

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

@dataclass
class _ListItem(object):
    """
    This class is used to store the information about a list item.
    """

    buffer: bytearray
    list_buffer_end: int = 0
    is_null: bool = False
    is_undefined = False
    type: int = DollarType.ITEM_PLACEHOLDER
    next_offset: int = 0
    data_offset: int = 0
    data_length: int = 0

    def __post_init__(self):
        # init list_buffer_end with the length of the buffer
        self.list_buffer_end = len(self.buffer)