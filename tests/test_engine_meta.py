from pydantic.main import BaseModel
from valueparser.parsers import Clipped, Formated
from valueparser.engine import Parsed, Parser

def test_meta_stack():

    class P(Parser[float, Clipped]):
        pass
    
    p = P(max=1.0)
    assert p.parse("2.0") == 1.0  

def test_meta_with_parse_def():
    class P(Parser[float]):
        class Config:
            max: float = 10.0
        @staticmethod
        def __parse__(value, config):
            return min( value, config.max)
    
    p = P()
    assert p.parse("3.0") == 3.0 
    assert p.parse("11.0") == 10.0
    p = P(max=1.0)
    assert p.parse("11.0") == 1.0


def test_parsed_in_pydantic():

    p = Parser[float, "Clipped"](min=0, max=1.0) 

    class M(BaseModel):
        x: Parsed[p] = 0.0 
        y: p.T = 0.0 
        
    m = M(x='3.0', y='10.0')
    assert m.x == 1.0
    assert m.y == 1.0 
