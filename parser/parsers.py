from typing import Any, Optional, Type, Union
from parser.engine import BaseParser
from enum import Enum, auto

import math

__all__ = ["Error", "ParseError", "Bounded"]


class Errors(Enum):
    OUT_OF_BOUND = auto()
    NOT_LISTED = auto() 

class ParseError(ValueError):
    def __init__(self, code, message):
        self.error_code = code
        super().__init__(message)
    
class Bounded(BaseParser):
    class Parameters(BaseParser.Parameters): 
        min: float = -math.inf
        max: float = math.inf
    
    @staticmethod
    def fparse(value: float, params: Parameters) -> float:        
        if value<params.min :
            raise ParseError(Errors.OUT_OF_BOUND, f'{value} is lower than {params.min}')
        if value>params.max :
            raise ParseError(Errors.OUT_OF_BOUND, f'{value} is higher than {params.max}')
        return value



class Clipped(BaseParser):
    class Parameters(BaseParser.Parameters):
        min: float = -math.inf
        max: float = math.inf
    
    @staticmethod
    def fparse(value: float, params: Parameters)-> float:
        return min(params.max,max(params.min, value))


class _Empty_:
    pass
_empty_ = _Empty_()

class Listed(BaseParser):
    class Parameters(BaseParser.Parameters):
        items: list = []
        default_item: Any = _empty_

    @staticmethod
    def fparse(value: Any, params: Parameters) -> Any:
        if value in params.items:
            return value
        if not isinstance(params.default_item, _Empty_):
            return params.default_item
        
        string_items = ", ".join( repr(i) for i in params.items) 
        raise ParseError(Errors.NOT_LISTED, f"item {value!r} is not in the list: {string_items} ") 
        


class Enumerated(BaseParser):
    class Parameters(BaseParser.Parameters):
        enumerator: Type[Enum]
    
    @staticmethod
    def fparse(value: Any, params: Parameters) -> Any:
        try:
            return params.enumerator(value)
        except ValueError as err:
            raise ParseError( Errors.NOT_LISTED, str(err))
        

class Rounded(BaseParser):
    class Parameters(BaseParser.Parameters):
        ndigits: Optional[int] = 0
    
    @staticmethod
    def fparse(value: float, params: Parameters) -> Union[int, float]:
        return round(value, params.ndigits) 

class Formated(BaseParser):
    class Parameters(BaseParser.Parameters):
        format: str = "%s"
    
    @staticmethod
    def fparse(value: float, params: Parameters) -> str:
        return params.format%( value, ) 


