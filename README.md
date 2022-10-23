# iris-list-python

Interpretor of $list for python named DollarList.

This interpretor was made because I wanted to use $list in python. And Embedded Python do not support $list.

This is a work in progress. For now it only support the parsing of $list. The next step is to make it work for writing $list.

# $list

## What is $list ?

$list is binary format for storing data. It is used in Iris Engine. It is a format that is easy to read and write. It is also easy to parse.

The neat thing about $list is that it is not limited for storage. It also used for communication on the SuperServer port of IRIS.

## How it works ?

$list is a binary format that store list of values. Each value is stored in a block. Each block is composed of a header and a body. The header is composed of a size and a type. The body is composed of the value.

### Header

The header is composed of a size and a type. 

#### Size

The size dictates the size of the block. The size is stored in `N` bytes.
`N` is determined by the number of bytes that are zero in the first bytes of the header.
The size is stored in little endian.

#### Type

The type is a byte that represent the type of the value. 
The type is stored just after the size.

List of types:
  * ascii: 0x01
  * unicode: 0x02
  * int: 0x04
  * negative int: 0x05
  * float: 0x06
  * negative float: 0x07
  * double: 0x08
  * compact double: 0x09

#### Body

The body is composed of the value.

To parse the body, you need to know the type of the value.

#### Ascii

Decode the value as ascii.

If decoding fails, consider the value as a sub-list.

If decoding the sub-list fails, consider the value as a binary.

#### Unicode

Decode the value as unicode.

#### Int

Parse the value as an integer in little endian and unsigned.

#### Negative Int

Parse the value as an integer in little endian and signed.

#### Float

????

#### Negative Float

????

#### Double

????

#### Compact Double

????

