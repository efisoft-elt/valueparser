from pydantic.main import BaseModel
import pytest
from parser import BaseParser, parser, parser_class, conparser


@pytest.fixture
def MyParser():
    class MyParser(BaseParser):
        class Parameters(BaseParser.Parameters):
            min: float = 0.0
    return MyParser

@pytest.fixture
def MinBound():
    class MinBound(BaseParser):
        class Parameters(BaseParser.Parameters):
            min: float = 0.0 
        @staticmethod
        def fparse(value, parameters):
            return max( value, parameters.min) 
    return MinBound

@pytest.fixture
def MaxBound():
    class MaxBound(BaseParser):
        class Parameters(BaseParser.Parameters):
            max: float = 1.0 
        @staticmethod
        def fparse(value, parameters):
            return min( value, parameters.max)
    return MaxBound


def test_base_parser_api():
    BaseParser.Parameters
    BaseParser.fparse
    BaseParser.parse 


def test_parser_class_from_callable():
    Int = parser_class( int, "Int" )
    assert Int().parse( 4.2) == 4

def test_parser_class_from_base_parser(MyParser):
    assert parser_class(MyParser) is MyParser 
    assert parser_class(MyParser, "Test") is not MyParser
    assert issubclass( parser_class(MyParser, "Test"), MyParser) 


def test_parser_class_from_list_of_callable():
    Parser = parser_class( [float, int])
    assert Parser().parse( "3.2") == 3

def test_parser_class_from_list_of_base_parser(MinBound, MaxBound):
     Parser = parser_class( [MinBound, MaxBound] )
     p = Parser( min=0, max=10)
     assert p.parse(2) == 2 
     assert p.parse(11) == 10 
     assert p.parse(-1) == 0

def test_parser_class_from_mixed_list(MinBound, MaxBound):
    Parser = parser_class( [float, int, MinBound, MaxBound] )
    p = Parser( min=0, max=10)
    assert p.parse('2.1') == 2 
    assert p.parse('11.34') == 10 
    assert p.parse(-1) == 0


def test_parser_class_from_instance_of_parser(MinBound, MaxBound):
    Parser = parser_class( MinBound(min=1))
    assert Parser().parse(0) == 1
    with pytest.raises(( ValueError, TypeError)):
        p = Parser( min=0)
    
    assert MinBound(min=1).parse(0) == 1

    Parser = parser_class( [MinBound(min=1), MaxBound])
    with pytest.raises(( ValueError, TypeError)):
        Parser( min=0)

    assert Parser(max=10).parse(0.0) == 1


def test_parser_function_with_callable():
    assert parser( int ).parse( 2.3) == 2

def test_parser_function_with_list_of_callable():
    assert parser( (float, int)).parse( "2.3") == 2

def test_parser_should_raise_value_error_for_unknown_kwargs():
    with pytest.raises( ValueError):
        parser( int, some_parameter=0)

def test_parser_should_accept_base_parser_class(MyParser):
    assert isinstance( parser(MyParser), BaseParser)

def test_parser_should_accept_kwargs_when_defined(MyParser):
    parser( MyParser, min=1.0) 
    with pytest.raises( ValueError):
        parser( MyParser, some_unknown_parameter=0)

def test_parser_with_mixed_list_and_keywords(MinBound, MaxBound):
    
    p = parser( [float, MinBound, MaxBound], min=0, max=10)
    assert p.parse( "2.3")== 2.3
    assert p.parse("11") == 10.0 
    with pytest.raises( ValueError):
        
        p = parser( [float, MinBound, MaxBound], min=0, max=10, some_unknown_parameter=0)

def test_parser_from_instance_of_parser(MinBound):
    assert parser(MinBound(min=1)).parse(0) == 1
    with pytest.raises( ValueError):
        parser(MinBound(min=1), min=0)

def test_parser_from_empty_list():
    assert parser([]).parse(1)==1


def test_conparser_in_model(MinBound, MaxBound):
    T = conparser([int])

    class M(BaseModel):
        x : conparser( [MinBound, MaxBound], min=0, max=10) = 5.0
        y : T = 0.0
    assert M( x=-1).x == 0
    assert M( x=11).x == 10
    assert M( y="23").y == 23
