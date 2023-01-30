
from valueparser import ParserFactory, Parser
from valueparser import  parser_class
from valueparser import parsers
from systemy import BaseSystem 


def test_factory_reference():

    class S(BaseSystem):
        class Config:
            parser = ParserFactory((float, parsers.Clipped), min=0, max=1)
            parser2: ParserFactory = None 
    
    s = S(  parser2 = {'type':(float, "Clipped"), 'min':0, 'max':1} )
    assert s.parser.parse("2") == 1
    assert s.parser2.parse("2") == 1


def test_parser_class():
    p = Parser[float, parsers.Clipped](min=0, max=1)
    assert p.parse("2") == 1

# test_parser_class()
test_factory_reference()
