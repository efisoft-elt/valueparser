from typing import Any, Optional, Type, Union
from valueparser.engine import Parser, parser_class, register_parser_factory
from enum import Enum, EnumMeta, auto
import datetime 
import math

__all__ = ["Errors", "ParseError", "Bounded", "Clipped", "Listed", "Enumerated", 
        "Default", "Rounded", "Formated", "Modulo", "Default", "Timestamp", "DateTime"
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
        register_parser_factory(Tpe, cls)
        register_parser_factory(tpe.__name__, cls)
        # record_class(cls, type=tpe.__name__)
        globals()[ Tpe ] = cls
        __all__.append( Tpe) 
_make_global_parsers([int, float, complex, bool, str, tuple, set, list])



@register_parser_factory    
class Bounded(Parser):
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
class Clipped(Parser):
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
class Listed(Parser):
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
class Enumerated(Parser):
    class Config:
        enumerator: Type[Enum]
    
    @staticmethod
    def __parse__(value: Any, params: Config) -> Any:
        try:
            return params.enumerator(value)
        except ValueError as err:
            raise ParseError( Errors.NOT_LISTED, str(err))

class _DumyError(Enum):
    pass 

@register_parser_factory
class Error(Parser):
    class Config:
        Error: Type[Enum] = _DumyError
        UNKNOWN: Enum = None 
    
    @staticmethod
    def __parse__(value: Any, params: Config) -> Any:
        try:
            return params.Error(value)
        except ValueError as err:
            if params.UNKNOWN is None:
                raise ParseError( Errors.NOT_LISTED, str(err))
            return params.UNKNOWN


@register_parser_factory
class Rounded(Parser[float]):
    class Config:
        ndigits: Optional[int] = 0
    
    @staticmethod
    def __parse__(value: float, params: Config) -> Union[int, float]:
        return round(value, params.ndigits) 

@register_parser_factory
class Formated(Parser):
    class Config:
        format: str = "%s"
    
    @staticmethod
    def __parse__(value: float, params: Config) -> str:
        return params.format%( value, ) 

@register_parser_factory
class Modulo(Parser[float]):
    class Config:
        modulo: int = 1

    @staticmethod
    def __parse__( value: float, params: Config) -> float:
        return value%params.modulo

@register_parser_factory
class Default(Parser):
    class Config:
        default: Any

    @staticmethod
    def __parse__( value: float, params: Config) -> float:
        if value is None:
            return params.default
        else:
            return value

@register_parser_factory
class Timestamp(Parser):
    """ parse a datetime, a string (ISO format) or a float to a timestamp float """
    class Config:
        time_offset : float = 0.0
    @staticmethod 
    def __parse__(value: Union[str, datetime.datetime, float], config: Config) -> float:
        if isinstance( value, datetime.datetime):
            time = value.timestamp()
        elif isinstance(value, str):
            time = datetime.datetime.fromisoformat( value).timestamp()
        elif isinstance( value, (float, int)):
            time =  float(value)
        else:
            raise ValueError(f"expecting a datetime, a str (ISO) or a float got a {type(value)}")
        return time+config.time_offset



@register_parser_factory
class DateTime(Parser):
    """ Parse a datetime, a string (ISO format) or a float(timestamp)  to a datetime object """
    @staticmethod
    def __parse__(value:  Union[str, datetime.datetime, float], config)-> datetime.datetime:
        if isinstance(value, datetime.datetime):
            return value 
        
        if isinstance(value, str):
            return datetime.datetime.fromisoformat(value)

        if isinstance(value, float):
            return datetime.datetime.fromtimestamp(value) 
        raise ValueError(f"expecting a datetime, a str (ISO) or a float got a {type(value)}")

