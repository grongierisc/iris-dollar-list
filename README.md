# iris-dollar-list

[![PyPI - Status](https://img.shields.io/pypi/status/dollar-list)](https://pypi.org/project/iris-dollar-list/)
[![PyPI](https://img.shields.io/pypi/v/dollar-list)](https://pypi.org/project/iris-dollar-list/)
[![GitHub](https://img.shields.io/github/license/grongierisc/dollar-list)](https://github.com/grongierisc/iris-dollar-list/blob/main/LICENSE)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dollar-list)](https://pypi.org/project/iris-dollar-list/)

Interpretor of $list for python named DollarList.

This interpretor was made because :
 * I wanted to use $list in python. 
 * Embedded Python do not support $list. 
 * The native API version do not support embedded $list in $list. 

This is a work in progress. For now it only support the parsing of $list with recursive $list.
The next step is to make it work for writing $list.

- [iris-dollar-list](#iris-dollar-list)
- [2. $list](#2-list)
  - [2.1. What is $list ?](#21-what-is-list-)
  - [2.2. How it works ?](#22-how-it-works-)
    - [2.2.1. Header](#221-header)
      - [2.2.1.1. Size](#2211-size)
      - [2.2.1.2. Type](#2212-type)
    - [2.2.2. Body](#222-body)
      - [2.2.2.1. Ascii](#2221-ascii)
      - [2.2.2.2. Unicode](#2222-unicode)
      - [2.2.2.3. Int](#2223-int)
      - [2.2.2.4. Negative Int](#2224-negative-int)
      - [2.2.2.5. Float](#2225-float)
      - [2.2.2.6. Negative Float](#2226-negative-float)
      - [2.2.2.7. Double](#2227-double)
      - [2.2.2.8. Compact Double](#2228-compact-double)
  - [Development](#development)

# 2. $list

## 2.1. What is $list ?

$list is binary format for storing data. It is used in Iris Engine. It is a format that is easy to read and write. It is also easy to parse.

The neat thing about $list is that it is not limited for storage. It also used for communication on the SuperServer port of IRIS.

## 2.2. How it works ?

$list is a binary format that store list of values. Each value is stored in a block. Each block is composed of a header and a body. The header is composed of a size and a type. The body is composed of the value.

### 2.2.1. Header

The header is composed of a size and a type. 

#### 2.2.1.1. Size

The size dictates the size of the block. The size is stored in `N` bytes.
`N` is determined by the number of bytes that are zero in the first bytes of the header.
The size is stored in little endian.

#### 2.2.1.2. Type

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

### 2.2.2. Body

The body is composed of the value.

To parse the body, you need to know the type of the value.

#### 2.2.2.1. Ascii

Decode the value as ascii.

If decoding fails, consider the value as a sub-list.

If decoding the sub-list fails, consider the value as a binary.

#### 2.2.2.2. Unicode

Decode the value as unicode.

#### 2.2.2.3. Int

Parse the value as an integer in little endian and unsigned.

#### 2.2.2.4. Negative Int

Parse the value as an integer in little endian and signed.

#### 2.2.2.5. Float

????

#### 2.2.2.6. Negative Float

????

#### 2.2.2.7. Double

????

#### 2.2.2.8. Compact Double

????


## Development


