from abc import ABC, abstractmethod, abstractproperty

from abc import abstractmethod
from typing import Any, Callable, List, Type, TypeVar, Generic
from pydantic import BaseModel, Extra, ValidationError
from pydantic.fields import ModelField

class AbcParser(ABC):
    @abstractmethod
    def parse(self, value):
        """ parse a value """

class BaseParser(AbcParser):
    def __init__(self, **kwargs):
        self.parameters = self.Parameters(**kwargs)
        
    class Parameters(BaseModel):
        class Config:
            extra = Extra.forbid
    
    @staticmethod        
    def fparse(value:Any, parameters: BaseModel):
        raise NotImplementedError("fparse")

    def parse(self, value):
        return self.fparse(value, self.parameters)

class CombinedParser(BaseParser):
    @classmethod
    def __fparses__(cls):
        return []
    @classmethod
    def fparse(cls, value, parameters):
        for f in cls.__fparses__():
            value = f(value, parameters)
        return value 

class CallableParser:
    def __init__(self, func: Callable):
        self._func = func
    
    def parse(self, value):
        return self._func(value)


def callable_to_fparse(func):
    """ convert a callable function with one argument to fparse compatible argument """
    def fparse(value, _):
        return func(value)
    return fparse

_parser_counter = 0
def auto_name(obj):
    global _parser_counter
    _parser_counter +=1
    return f"Parser{_parser_counter:03f}"



def combine_parameter_class(lst: list, name) -> Type:
    #subclasses = [CombinedParser.Parameters]
    subclasses = []
    for obj in lst:
        if isinstance( obj, type):
            try:
                Parameters = obj.Parameters
            except AttributeError:
                continue
            subclasses.append( Parameters)
    subclasses = subclasses or [CombinedParser.Parameters]
    return type(name+"Parameters", tuple(subclasses), {})

def parser_class_from_list( lst, name):
    fparses = []
    for obj in lst:
        if isinstance(obj, type):
            if hasattr(obj, "fparse"):
                fparses.append( obj.fparse)
            elif hasattr(obj, "parse"):
                fparses.append( callable_to_fparse(obj.parse) )
            elif hasattr(obj, "__call__"):
                fparses.append( callable_to_fparse(obj) )
        elif hasattr(obj, "parse"):
            fparses.append( callable_to_fparse(obj.parse) )   
        else:
            raise ValueError(f"bad argument for parser_class {obj!r}")
    def __fparses__(cls):
        return fparses
    Parameters = combine_parameter_class(lst, name)
    return type( name, (CombinedParser, ), {"__fparses__":classmethod(__fparses__), "Parameters":Parameters})
        
    

def parser_class(obj, name=None):
    
    if isinstance( obj, type) and hasattr(obj, "parse"):
        if name is None:
            return obj 
        return type( name, (obj,),  {})

    if name is None:
        name = auto_name(obj)
    
    
    if hasattr(obj, "__call__"):
        return type(name , tuple(), {"parse": staticmethod(obj)})
    
    if hasattr(obj, 'parse'):
        return type(name , tuple(), {"parse": staticmethod(obj.parse)})

    if hasattr(obj, "__iter__"):
        return  parser_class_from_list(obj, name)

    raise ValueError("Bad Argument for parser_class")

def parser(obj, **kwargs):
    if isinstance(obj, type) and hasattr(obj, "parse"):
        return obj(**kwargs)

    if hasattr(obj, "__call__"):
        if kwargs:
            raise ValueError("parser from a callable does not accept kwargs")
        return CallableParser(obj)
    if hasattr(obj, "__iter__"):
        Parser = parser_class( obj)
        return Parser( **kwargs)
    if hasattr(obj, "parse"):
        if kwargs:
            raise ValueError("parser from a Parser Class does not accept kwargs")

        return obj
    raise ValueError("bad argument for parser")



#

ParserVar = TypeVar('ParserVar')
class _ParserTyping(Generic[ParserVar]):
    @classmethod
    def __parse__(cls, value):
        return value
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        pass

    @classmethod
    def validate(cls, v, field: ModelField):
        
        errors = []

        if field.sub_fields:
            if len(field.sub_fields)>1:
                raise ValidationError(['to many field conparser() built type require and accept only one argument'], cls)
            val_f = field.sub_fields[0]
                       
            valid_value, error = val_f.validate(v, {}, loc='value')
            
            if error:    
                errors.append(error)
        else:
            val_f = v

        if errors:
            raise ValidationError(errors, cls)

        valid_value = cls.__parse__(val_f)
        
        return valid_value
    
    def __repr__(self):
        return f'{self.__class__.__name__}({super().__repr__()})'


def conparser(obj, **kwargs):
    built_parser = parser( obj, **kwargs)
    subclasses =  (_ParserTyping,) 


    return type( built_parser.__class__.__name__+"Type", subclasses, 
                 {"__parse__": staticmethod(built_parser.parse)}
            )
