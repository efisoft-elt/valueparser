Parser
======

Python package for quick creation/ combination of value parser object for muly-puposes

Install
=======

```shell
> pip install valueparser
```

Usage
=====

```python
from valueparser.parsers import Bounded

value_parser = Bounded(min=0, max=1)

value_parser.parse(4.0)

# ParseError: 4.0 is higher than 1.0
```

Several parsers can be combined to one single parser object, they share however the same name space for configuration
parameters

```python 
from valueparser import parser, Clipped, Rounded

ratio_parser = parser( (float, Clipped, Rounded),  min=0, max=1.0, ndigits=2 )

assert ratio_parser.parse( 0.231234) == 0.23 
assert ratio_parser.parse( 4.5) == 1.0 
assert ratio_parser.parse( "0.12345") == 0.12

```

Equivalent can be done by creating a new class 

```python 
from valueparser import parser_class, Clipped, Rounded

MyParser = parser_class( (float, Clipped, Rounded), "MyParser" )
ratio_parser = MyParser( min=0, max=1, ndigits=2)
```


`conparser` works the same way than `parser` except it construct a typing object to be use inside pydantic BaseModel in
a compact way.


```python 
from valueparser import conparser, Bounded
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
from valueparser import parser

float_parser = parser(float)
assert float_parser.parse("1.234") == 1.234

force_int_parser = parser( (float, int)) # parse to float then int 
assert force_int_parser.parse( "1.234") == 1
```

Actually the `parser` function accepts :

- A Parser Class iddentified as a class with the `parse` method 
- A callable 
- An instance of a Parser Class
- an mix inside an iterable 

Plus any kwargs accepted by the combination of parsers

Builtin Parsers 
===============

| class name |  kwargs | comment | 
|------------|---------|---------|
| Bounded    | min=-inf, max=+inf | raise an error if value outside interval else return value |
| Clipped    | min=-inf, max=+inf | clip silently the value to inferior and superior bounds | 
| Rounded    | ndigits=0          | round the numerical value to ndigits           |
| Formated   | format="%s"        | convert to string with the given format        |
| Listed     | items=[], default_item(optional) |  raise error if value not in items list else return value a
|            |                                  | default_item can be set to be returned instead of error raised |
| Enumerated  | enumerator                        | return enumerator(value) or raise error | 


Create a custom parser
======================

To create a parser one need to create a new class from BaseParser, declare any configurable argument 
inside the child class ``Config``  and define the static or classmethod `__parse__`

For instance a parser adding some noise to a value ( can be usefull for e.i. a simulator) 

```python
from valueparser import BaseParser
import random 

class Noisier(BaseParser):
    class Config:
        noise_scale = 1.0
    @staticmethod
    def __parse__( value, config):
        return value + (random.random()-0.5) * config.noise_scale
```

Usage : 

```python
noisier = Noisier( noise_scale=100)
x = noisier.parse(0.0)
x
36.700125482238036
```

Or use conparser in pydantic Model: 

```python 
from valueparser import conparser 
from pydantic import BaseModel  

class MyData(BaseModel):
    x: conparser(Noisier, noise_scale=100)
    y: conparser(Noisier, noise_scale=100)

my_data = MyData(x=0, y=0)
my_data
MyData(x=32.819723479459284, y=-25.95893228872207)
```


Parser and Systemy 
==================

Parsers are beased on :class:`systemy.System` class. One can include a parser factory in 
a systemy class and expose the parser configuration to user. 

```python 
from valueparser import ParserFactory , Bounded
from systemy import BaseSystem 
from pydantic import AnyUrl 

dummy = lambda x:x 

class Node(BaseSystem):
    class Config:
        url: AnyUrl = "http://localhost:4840"
        parser: ParserFactory = ParserFactory(type=dummy)

    def set(self, value):
        value = self.parser.parse(value) 
        # set value on server 
        return value

node = Node( parser={'type':(float,Bounded), 'min':0, 'max':10} )
```







