from typing import Any, Optional, Type, Union
from valueparser.engine import BaseParser, parser_class, register_parser_factory
from enum import Enum, auto

import math

__all__ = ["Errors", "ParseError", "Bounded", "Clipped", "Listed", "Enumerated", 
        "Default", "Rounded", "Formated", "Modulo", "Default"
        ]


class Errors(Enum):
    OUT_OF_BOUND = auto()
    NOT_LISTED = auto() 

class ParseError(ValueError):
    def __init__(self, code, message):
        self.error_code = code
        super().__init__(message)



def _make_global_parsers(types):
    """ Build automaticaly some parser from python types """
    for tpe in types:        
        Tpe = tpe.__name__.capitalize()
        
        cls = parser_class(tpe, name=Tpe) 
        register_parser_factory(cls)
        register_parser_factory(tpe.__name__, cls)
        # record_class(cls, type=tpe.__name__)
        globals()[ Tpe ] = cls
        __all__.append( Tpe) 
_make_global_parsers([int, float, complex, bool, str, tuple, set, list])



@register_parser_factory    
class Bounded(BaseParser):
    class Config:
        min: float = -math.inf
        max: float = math.inf
    
    @staticmethod
    def __parse__(value: float, params: Config) -> float:        
        if value<params.min:
            raise ParseError(Errors.OUT_OF_BOUND, f'{value} is lower than {params.min}')
        if value>params.max :
            raise ParseError(Errors.OUT_OF_BOUND, f'{value} is higher than {params.max}')
        return value

@register_parser_factory
class Clipped(BaseParser):
    class Config:
        min: float = -math.inf
        max: float = math.inf
    
    @staticmethod
    def __parse__(value: float, params: Config)-> float:
        return min(params.max,max(params.min, value))


class _Empty_:
    pass
_empty_ = _Empty_()


@register_parser_factory
class Listed(BaseParser):
    class Config:
        items: list = []
        default_item: Any = _empty_

    @staticmethod
    def __parse__(value: Any, params: Config) -> Any:
        if value in params.items:
            return value
        if not isinstance(params.default_item, _Empty_):
            return params.default_item
        
        string_items = ", ".join( repr(i) for i in params.items) 
        raise ParseError(Errors.NOT_LISTED, f"item {value!r} is not in the list: {string_items} ") 


@register_parser_factory
class Enumerated(BaseParser):
    class Config:
        enumerator: Type[Enum]
    
    @staticmethod
    def __parse__(value: Any, params: Config) -> Any:
        try:
            return params.enumerator(value)
        except ValueError as err:
            raise ParseError( Errors.NOT_LISTED, str(err))
        
@register_parser_factory
class Rounded(BaseParser):
    class Config:
        ndigits: Optional[int] = 0
    
    @staticmethod
    def __parse__(value: float, params: Config) -> Union[int, float]:
        return round(value, params.ndigits) 

@register_parser_factory
class Formated(BaseParser):
    class Config:
        format: str = "%s"
    
    @staticmethod
    def __parse__(value: float, params: Config) -> str:
        return params.format%( value, ) 

@register_parser_factory
class Modulo(BaseParser):
    class Config:
        modulo: int = 1

    @staticmethod
    def __parse__( value: float, params: Config) -> float:
        return value%params.modulo

@register_parser_factory
class Default(BaseParser):
    class Config:
        default: Any

    @staticmethod
    def __parse__( value: float, params: Config) -> float:
        if value is None:
            return params.default
        else:
            return value


