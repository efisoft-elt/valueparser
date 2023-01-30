import pytest 
from enum import Enum
import datetime
from valueparser import ParseError, parser
from valueparser import Bounded
from valueparser import Clipped
from valueparser import Listed
from valueparser import Enumerated
from valueparser import Rounded
from valueparser import Formated
from valueparser import Modulo
from valueparser import Default, Int
from valueparser.parsers import DateTime, Error, Timestamp



def test_type_parser():
    p = parser("int")
    assert p.parse(2.3) == 2
    p = parser("Int")
    assert p.parse(2.3) == 2
    p = parser(Int)
    assert p.parse(2.3) == 2
p = parser("int")
assert p.parse(2.3) == 2
p = parser("Int")
assert p.parse(2.3) == 2
p = parser(Int)
assert p.parse(2.3) == 2

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


def test_modulo_parser():
    p = Modulo( modulo=2)
    assert p.parse(2)==0
    assert p.parse(1)==1 
    assert p.parse(3)==1

def test_default_parser():
    p = Default( default=10)
    assert p.parse( None ) == 10 
    assert p.parse( 0) == 0 
    assert p.parse( 2) == 2


def test_timestamp():

    p = Timestamp()
    assert p.parse( datetime.datetime( 1970, 1, 1, 1)) == 0.0 
    assert p.parse( '1970-01-01T01:00:00') == 0.0 
    assert p.parse( 1.0 ) == 1.0

def test_datetime():
    p = DateTime()
    d = datetime.datetime( 1970, 1, 1, 1)
    assert p.parse(d ) == d
    assert p.parse( '1970-01-01T01:00:00') == d 
    assert p.parse(0.0) == d
   
def test_error():
    class E(int, Enum):
        BAD_VALUE = 1
        BAD_KEY = 2 
        UNKNOWN = -9999
    p = Error( Error=E, UNKNOWN=E.UNKNOWN)
    assert p.parse(1) is E.BAD_VALUE
    assert p.parse(10) is E.UNKNOWN

    p = Error( Error=E)
    with pytest.raises( ValueError):
        p.parse(10)


