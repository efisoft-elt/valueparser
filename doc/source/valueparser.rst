What is it ? 
============


- a python module 
- an engine to easely build and combine parser methods 
- a collection of Parsers to be used 

A :class:`valueparser.Parser` is an object with a parse method which can be 
use in several context to parse an input, e.g. change type, control its range, etc ... 

This is base on :mod:`systemy`, it uses :mod:`pydantic` and can be integrated in some 
pydantic model.  




Installation 
============

::

    > pip install valueparser 

The sources can alternatively be found here https://github.com/efisoft-elt/valueparser


Usage 
=====


Bellow an example on how to use a builtin parser class. In this example `Clipped` is clipping 
data with a min and max argument. 

.. code-block:: python 

   import valueparser.parsers as ps 
   pixel = ps.Clipped(min=0, max=1023)
    
   assert pixel.parse(10) == 10
   assert pixel.parse(1240) == 1023 


However, following this example, it might be useful to first parse the input has an integer first. 
The simple and normal way would be to subclass the `Clipped` class. But valueparser aims to do that 
for you in a simple but elegant way: 

.. code-block:: python 
    
    from valueparser import Parser, parsers as ps 
    pixel = Parser[int,ps.Clipped](min=0, max=1023)
    
    assert pixel.parse(10.2123) == 10
    assert pixel.parse(1240.32) == 1023 


On can use directly the `Parser` class to build new classes with the `[]` protocol. 
As show above, `Parser[int, ps.Clipped]` is building a 
new Parser class, then the new class is instantiated with arguments brought by the `Clipped` Parser. 

Note that each stacked classes will share the same namespace for arguments. 

`Parser` accept several input kinds :

- an other Parser class 
- a type (e.g. int, float, list, etc ...), the type must accept one and one only positional argument 
- a callable object, must accept one and one only positional argument
- a string, valueparser will try to find a registered parser with that name. This can be useful when 
    the parser definition is coming from externam payload (yaml, json, etc.. )
    following above example :  Parser[int, "Clipped"] also works. 


Contrary to pydantic, valueparser does not try to do data validation from different data kinds. 
Therefore, something like `Parser[Union[int,str]]` will not work. See pydantic for this kind of job. 

Usage inside pydantic BaseModel
================================

.. code-block:: python 
    
    from valueparser import Parser 
    from pydantic import BaseModel 

    pixel = Parser[float, int,"Clipped"](min=0, max=1023)
    
    class PixelCoordinates(BaseModel):
        x: pixel.T = 0 
        y: pixel.T = 0 

    c = PixelCoordinates( x="23.1", y=1148) 
    assert c.x == 23 
    assert c.y == 1023



Notes 
=====

The goal of :mod:`valueparser` is really to save a moderate amount on codding, the goal is to have a
collection of :class:`Parser` and make assemblies. 

For instance, something like : 

.. code-block:: python 

    class Pixel(Clipped):
        def parse(self, value):
            value = int(float(value))
            return super().parse(value)
    pixel = Pixel(min-0, max=1023)
    
Is replaced by: 

.. code-block:: python 

   Pixel = Parser[float, int, Clipped](min-0, max=1023)

I am guessing that still this compact form is human readable and easy to understand. 


Make a custom Parser class
========================== 

Two rules : 

- parameters are added inside a Config (sub-)class (which is transformed to a BaseModel)
- the method  `__parse__` must be implemented as staticmethod  



.. code-block:: python 
    
    from valueparser import Parser, register_parser_factory 
    from typing import List  

    @register_parser_factory("TeamName")
    class TeamNameParser(Parser[str ]):
        class Config:
            names: List[str] = []
            default: str = "Anonymous" 
        
        @staticmethod
        def __parse__(value, config):
            if value in config.names:
                return value 
            return config.default 
    
    name_parser  = TeamNameParser( names=["Silvia" , "John", "Luc"])
    assert name_parser.parse( "Michael") == name_parser.default 

    
see :mod:`systemy` for explanations of how the Config class works.    
