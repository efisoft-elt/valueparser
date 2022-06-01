Parser
======

Python package for quick creation/ combination of parser object for muly-puposes

Install
=======

```shell
> pip install parser
```

Usage
=====

```python
from parser import Bounded

value_parser = Bounded(min=0, max=1)

value_parser.parse(4.0)

# ParseError: 4.0 is higher than 1.0
```

Several parsers can be combined to one single parser object, they share however the same name space for configuration
parameters

```python 
from parser import parser, Clipped, Rounded

ratio_parser = parser( (float, Clipped, Rounded),  min=0, max=1.0, ndigits=2 )

assert ratio_parser.parse( 0.231234) == 0.23 
assert ratio_parser.parse( 4.5) == 1.0 
assert ratio_parser.parse( "0.12345") == 0.12

```

Equivalent can be done by creating a new class 

```python 
from parser import parser_class, Clipped, Rounded

MyParser = parser_class( (float, Clipped, Rounded), "MyParser" )
ratio_parser = MyParser( min=0, max=1, ndigits=2)
```


`conparser` works the same way than `parser` except it construct a typing object to be use inside pydantic BaseModel in
a compact way.


```python 
from parser import conparser, Bounded
from pydantic import BaseModel 

Pixel =  conparser( (int, Bounded), min=0, max=1023 ) 
class Data(BaseModel):
    x: Pixel = 512
    y: Pixel = 512
   
Data(x=-200)

# 
#pydantic.error_wrappers.ValidationError: 1 validation error for Data
#x
#    -200.0 is lower than 0.0 (type=value_error.parse; error_code=Errors.OUT_OF_BOUND)
```

to make any function a `parser` (e.g. an object with `parse` method) one can use the  `parser` function as well :

```python
from parser import parser

float_parser = parser(float)
assert float_parser.parse("1.234") == 1.234

force_int_parser = parser( (float, int)) # parse to float then int 
assert force_int_parser.parse( "1.234") == 1
```
