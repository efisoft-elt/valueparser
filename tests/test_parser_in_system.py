
from valueparser import parser_factory , parser_class
from valueparser import parsers
from systemy import BaseSystem 


def test_factory_reference():

    class S(BaseSystem):
        class Config:
            parser = parser_factory((float, parsers.Clipped), min=0, max=1)
    
    s = S()
    assert s.parser.parse("2") == 1

def test_parser_class():
    p = parser_class((float, parsers.Clipped))(min=0, max=1)
    assert p.parse("2") == 1

# test_parser_class()
test_factory_reference()
