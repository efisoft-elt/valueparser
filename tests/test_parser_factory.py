from typing import List, Optional
import pytest 
from valueparser import Bounded, Rounded, Clipped,  ParserFactory, parser
from systemy import BaseSystem 

def test_parser_factory_args():

    p = ParserFactory( type=[float, Clipped], min=0, max=10).build()
    assert p.parse( "1") == 1
    assert p.parse(11) == 10
    
def test_extra_args_shall_raise_error():
    with pytest.raises( ValueError):
        f = ParserFactory( type=[float, Clipped], min=0, max=10, extra_arg=None)

def test_factory_from_callable():
    dummy = lambda x:x 
    f = ParserFactory(type=dummy)
    assert f.build().parse(1.0) == 1.0 

def test_factory_inside_systemy():
    class S(BaseSystem):
        class Config:
            parser: ParserFactory = ParserFactory(type=float)
    assert S().parser.parse(1) == 1.0


def test_factory_inside_system_with_parser_config():
    class S(BaseSystem):
            class Config:
                parser: Optional[ParserFactory] = None 

    s = S( parser = Clipped.Config(max=1.0))
    assert s.parser.parse(2.0) == 1.0  
    s = S( parser = Clipped(max=1.0))
    assert s.parser.parse(2.0) == 1.0  

def test_factory_inside_system_with_callable():
    class S(BaseSystem):
        class Config:
            parser: Optional[ParserFactory] = None 
    s = S(parser=lambda x: x+1)
    assert s.parser.parse(1) == 2

def test_parser_factory_as_dict():
    p = ParserFactory( dict(type=[float, Clipped], min=0, max=10)).build()
    assert p.parse( "1") == 1
    assert p.parse(11) == 10
    

    

def test_parser_factory_list():

    class S(BaseSystem):
        class Config:
            parsers: List[ParserFactory] = []

    s = S( parsers=[int,int]) 
    assert [p.parse(a) for p,a in zip(s.parsers, ["1", "2"])] == [1, 2]
    
    s = S( parsers=[int,{'type':"Clipped", "min":0, "max":2}])
    assert s.parsers[1].parse(3.4) == 2.0 

def test_factory_with_func():
    class S(BaseSystem):
        class Config:
            parser: Optional[ParserFactory] = []
    s = S(parser=parser(float))
    assert s.parser.parse("1.0") == 1.0

def test_factory_with_func():
    class S(BaseSystem):
        class Config:
            parser: Optional[ParserFactory] = []
    s = S(parser=parser((float, Clipped)))
    assert s.parser.parse("1.0") == 1.0
