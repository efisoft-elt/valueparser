import pytest 
from enum import Enum 
from parser import ParseError
from parser import Bounded
from parser import Clipped
from parser import Listed
from parser import Enumerated
from parser import Rounded
from parser import Formated

def test_bounded_parser():
    p = Bounded()

    assert p.parse( 1e99) == 1e99
    
    p = Bounded( min=0, max=10)
    assert p.parse( 2) == 2
    with pytest.raises( ParseError):
        p.parse(12)


def test_clipped_parser():

    p = Clipped()
    assert p.parse( 1e99) == 1e99
    p = Clipped( min=0, max=10)
    assert p.parse( 2) == 2
    assert p.parse( 11) == 10

def test_listed_parser():

    p = Listed( items=list("ABCDEF"))
    assert p.parse("C") == "C"
    with pytest.raises( ParseError ):
        p.parse("Z")

    p = Listed( items=list("ABCDEF"), default_item="Z")
    assert p.parse("W") == "Z"


def test_enumerated_parser():
    class E(int, Enum):
        A = 1
        B = 2  
        C = 3
        
    p = Enumerated(enumerator=E)
    assert p.parse(1) == 1 


def test_rounded_parser():
    p = Rounded( ndigits=2)
    assert p.parse( 2.1234) == 2.12 
    p = Rounded( ndigits=None)
    assert isinstance( p.parse(2.3), int)

def test_formated_parser():
    
    p = Formated( format="%.3f")
    assert p.parse( 1.123456) == "1.123"
    with pytest.raises(TypeError):
        p.parse( "abcd") 
    p = Formated()
    assert p.parse( (1,2) ).replace(" ", "") == "(1,2)"




