# 1. iris-dollar-list

[![PyPI - Status](https://img.shields.io/pypi/status/iris-dollar-list)](https://pypi.org/project/iris-dollar-list/)
[![PyPI](https://img.shields.io/pypi/v/iris-dollar-list)](https://pypi.org/project/iris-dollar-list/)
[![GitHub](https://img.shields.io/github/license/grongierisc/iris-dollar-list)](https://github.com/grongierisc/iris-dollar-list/blob/main/LICENSE)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/grongierisc/de6821ab77160e603e25e79f847d9863/raw/covbadge.json)](https://github.com/grongierisc/iris-dollar-list/actions)

Interpretor of $list for python named DollarList.

This interpretor was made because :
 * I wanted to use $list in python. 
 * Embedded Python do not support $list. 
 * The native API version do not support embedded $list in $list. 

This is a work in progress. For now, it only support embedded $list in $list, int and string.

WIP float,decimal,double

  **This module is available on Pypi :**

```sh
pip3 install iris-dollar-list
```

It is compatible with embedded python and native api.

## 1.1. Table of Contents

- [1. iris-dollar-list](#1-iris-dollar-list)
  - [1.1. Table of Contents](#11-table-of-contents)
  - [1.2. Usage](#12-usage)
  - [1.3. functions](#13-functions)
    - [1.3.1. append](#131-append)
    - [1.3.2. from_bytes](#132-from_bytes)
    - [1.3.3. from_list](#133-from_list)
    - [1.3.4. from_string](#134-from_string)
    - [1.3.5. to_bytes](#135-to_bytes)
    - [1.3.6. to_list](#136-to_list)
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
  - [2.3. Development](#23-development)

## 1.2. Usage

example :

```objectscript
set ^list = $lb("test",$lb(4))
```

example of use with native api : 
 

```python
import iris
from iris_dollar_list import DollarList
 
conn = iris.connect("localhost", 57161,"IRISAPP", "SuperUser", "SYS")
 
iris_obj = iris.createIRIS(conn)
 
gl = iris_obj.get("^list")
 
my_list = DollarList.from_bytes(gl.encode('ascii'))
 
print(my_list.to_list())
# ['test', [4]]
```

example of use with embedded python :

```python
import iris
from iris_dollar_list import DollarList
 
gl = iris.gref("^list")
 
my_list = DollarList.from_bytes(gl[None].encode('ascii'))
 
print(my_list.to_list())
# ['test', [4]]
```

## 1.3. functions

###  1.3.1. append

Append an element to the list.

This element can be :
 * a string
 * an int
 * a DollarList
 * a DollarItem

```python
my_list = DollarList()
my_list.append("one")
my_list.append(1)
my_list.append(DollarList.from_list(["list",2]))
my_list.append(DollarItem(dollar_type=1, value="item",
                          raw_value=b"item",
                          buffer=b'\x06\x01item'))
print(DollarList.from_bytes(my_list))
# $lb("one",1,$lb("list",2),"item")
```

###  1.3.2. from_bytes

Create a DollarList from bytes.

```python
my_list = DollarList.from_bytes(b'\x05\x01one')
print(my_list)
# $lb("one")
```

###  1.3.3. from_list

Create a DollarList from a list.

```python
print(DollarList.from_list(["list",2]))
# $lb("list",2)
```

### 1.3.4. from_string

Create a DollarList from a string.

```python
str_list = DollarList.from_string('$lb("test",$lb(4))')
print(str_list)
# $lb("test",$lb(4))
print(str_list.to_list())
# ['test', [4]]
```

###  1.3.5. to_bytes

Convert the DollarList to bytes.

```python
my_list = DollarList.from_list(["list",2])
print(my_list.to_bytes())
# b'\x06\x01list\x03\x04\x02'
```

###  1.3.6. to_list

Convert the DollarList to a list.

```python
my_list = DollarList.from_bytes(b'\x05\x01one')
print(my_list.to_list())
# ['one']
```

# 2. $list

## 2.1. What is $list ?

$list is binary format for storing data. It is used in Iris Engine. It is a format that is easy to read and write. It is also easy to parse.

The neat thing about $list is that it is not limited for storage. It also used for communication on the SuperServer port of IRIS.

## 2.2. How it works ?

$list is a binary format that store list of values. Each value is stored in a block. Each block is composed of a header and a body. The header is composed of a size and a type. The body is composed of the value.

### 2.2.1. Header

The header is composed of a size and a type. 
The header can have a size of 2, 4 or 8 bytes.

Three types of header are possible :
 * 2 bytes header
   * 1 byte for the size
   * 1 byte for the type
 * 4 bytes header
   * 1 bytes of \x00
   * 2 bytes for the size
   * 1 byte for the type
 * 8 bytes header
   * 3 bytes of \x00
   * 4 bytes for the size
   * 1 byte for the type

#### 2.2.1.1. Size

There is 3 types of size :
 * 1 byte, if the first byte is not \x00
 * 2 bytes, if the first byte is \x00 and the int value of the second two bytes is not 0
 * 4 bytes, else (the first 3 bytes are \x00)

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


## 2.3. Development


