from abc import ABC, ABCMeta, abstractmethod, abstractproperty

from abc import abstractmethod
from typing import Any, Callable, Iterable, List, Type, TypeVar, Generic, Union
from pydantic import BaseModel, Extra, ValidationError, root_validator
from pydantic.fields import ModelField
from pydantic.main import create_model

from systemy import BaseSystem, BaseFactory, register_factory, get_factory_class, storedproperty

PARSER_NAMESPACE = "parser"
PARSER_KIND = "Parser"

# # ## ## ## ## ## ## ## ## # ## ## ## ## ## ### ## ## ## ## ## ## ## ## # ## ## ###

class ParserFactory(BaseFactory):
    type: Union[str,Callable, Type, BaseFactory, List[Union[str,Callable,Type]]]
    class Config:
        extra = "allow"
    
    def __init__(self, type, **kwargs):
        if isinstance(type, dict):
            kwargs = {**type, **kwargs}
            type = kwargs.pop("type")
        super().__init__(type=type, **kwargs)
    
    @classmethod
    def parse_obj(cls, obj):
        if not isinstance(obj, dict):
            obj = {'type':obj}
        return super().parse_obj(obj)

    def build(self, parent=None, name=None):
        return parser( self.type, **self.dict( exclude={'type'}) ) 
    
    @root_validator
    def _check_args_validator(cls, values):
        kws = values.copy()
        type_ = kws.pop("type", None)
        if type_:
            parser( type_, **kws)
        return values 
    
    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate
    
    @classmethod
    def validate(cls, v, field: ModelField):
        if field.sub_fields:
           raise ValueError("ParserFactory does not accept sub-fields") 
        if isinstance(v, ParserFactory):
            return v
        if isinstance(v, Parser.Config):
            return v
        if isinstance(v, Parser):
            return v.__config__
        return ParserFactory(v)





def _callable_to_fparse(func):
    """ convert a callable function with one argument to __parse__ compatible argument """
    def __parse__(value, _):
        return func(value)
    return __parse__


def _build_parser_class(cls_, items, name=None,  **config_kwargs):
    parsers = list( cls_.__iter_parsers__() )
    classes = []
    if isinstance(items, str):
        items = (items,)
    elif isinstance( items, type):
        items = (items,)
    elif isinstance( items, cls_):
        items = (items,)
    elif not hasattr( items, "__iter__"):
        items = (items,)
     
    for cls in items:
        if isinstance( cls, str):
            cls = get_parser_factory_class(cls).get_system_class()

        if isinstance( cls, type):
            if hasattr( cls, "__iter_parsers__"):
                itp = cls.__iter_parsers__
                parsers.extend( itp() )
                classes.append(cls.Config) 
            elif hasattr( cls, "__call__"):
                    parsers.append( _callable_to_fparse(cls)) 
        else:
            if isinstance( cls, cls_):
                parsers.append( _callable_to_fparse(cls.parse)) 
            elif hasattr( cls, "__call__"):
                parsers.append( _callable_to_fparse(cls)) 


    def __iter_parsers__(cls):
        for p in cls.__parsers__: 
            yield p 
        if cls.__parse__:
            yield cls.__parse__ 

    kwargs = {}
    kwargs["__iter_parsers__"] = classmethod( __iter_parsers__)
    kwargs["__parsers__"] = tuple(parsers)
    kwargs["__parse__"] = None
    if classes:
        kwargs["Config"] = create_model(
                "Config", 
                __base__=tuple(classes), 
                **config_kwargs
            )
    name = _auto_name() if not name else name 
    return type(name, (cls_,), kwargs) 


class ParserMeta(type(BaseSystem)):
    def __getitem__(cls_, items):
       return _build_parser_class(cls_, items) 


class Parser(BaseSystem, metaclass=ParserMeta):
    class Config:
        ...
    
    @classmethod
    def __iter_parsers__(cls):
        yield cls.__parse__
    
    @staticmethod        
    def __parse__(value:Any, config: Config):
        return value
        # raise NotImplementedError("__parse__")

    def parse(self, value):
        for p in self.__iter_parsers__():
            value = p(value, self.__config__)
        return value   
    
    @storedproperty
    def T(self):
        return Parsed[self] 

    
    
BaseParser = Parser 

_parser_counter = int(0)
def _auto_name(obj=None):
    global _parser_counter
    _parser_counter +=1
    return f"Parser{_parser_counter:03d}"


def register_parser_factory(name, cls=None) -> None:
    return register_factory(name, cls, kind=PARSER_KIND)

def get_parser_factory_class(name) -> BaseFactory:
    return get_factory_class(name, kind=PARSER_KIND)

def parser_class(
            obj: Union[Callable, Type, str, Iterable[Union[Callable, Type, str]] ], 
            name: str = None
        ) -> Type:
    """ Build a new parser class for various inputs types 

    Args:
        obj: can be
            - a callable  (e.g. int ) 
            - a parser object: an object with the ``parse`` method  
            - a :class:`BaseParser` (which is returned as is if name is None)  
            - an iterable of a mix of above object kind
        name (str, optional): is the new class name. If not given one is created.  
    """
    if isinstance( obj, type):
        if issubclass(obj, Parser):
            if name is None:
                return obj 
    if isinstance(obj, str):
        return get_factory_class(obj).get_system_class() 

    return  _build_parser_class( Parser, obj, name=name)


def parser_factory_class(obj, name=None):
    Parser = parser_class(obj, name)
    def build(self, parent=None, name=""):
        path = self._make_new_path(parent, name)
        return Parser( __config__= self, __path__=path)
    return type( Parser.__name__+"Factory", (Parser.Config,), {"build": build})

def parser_factory(obj, **kwargs):
    return parser_factory_class(obj)(**kwargs)

def parser(obj, **kwargs):
    return parser_class(obj)(**kwargs)

#



class ParsedMeta(type):
    def __getitem__(cls, parser):
        if isinstance( parser, tuple):
            if len(parser) == 1:
                parser, = parser 
            else:
                raise ValueError( "Parsed[parser] accept only one item, a Parser ")
        
        return type( cls.__name__+str(id(parser)), (cls, ), {'__parser__':parser})

class Parsed(metaclass=ParsedMeta):
    __parser__ = None 
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value, field: ModelField):
        if field.sub_fields:
            raise ValidationError(['to many sub-field'], cls)
        if cls.__parser__ is None:
            return value 
        return cls.__parser__.parse( value )
        

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
    """ Build a field annotation for pydantic model 

    Exemple:
        
        from pydantic import BaseModel 
        from parser import conparser, Bounded
        
        Pixel = conparer( (int, Bounded), min=0, max=1023 )
    
        class Model(BaseModel):
            x: Pixel = 512
            y: Pixel = 512
    """
    built_parser = parser( obj, **kwargs)
    subclasses =  (_ParserTyping,) 

    return type( built_parser.__class__.__name__+"Type", subclasses, 
                 {"__parse__": staticmethod(built_parser.parse)}
            )




