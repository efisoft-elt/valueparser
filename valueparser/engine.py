from abc import ABC, abstractmethod, abstractproperty

from abc import abstractmethod
from typing import Any, Callable, Iterable, List, Type, TypeVar, Generic, Union
from pydantic import BaseModel, Extra, ValidationError, root_validator
from pydantic.fields import ModelField

from systemy import BaseSystem, BaseFactory, systemclass, register_factory, get_factory_class

PARSER_NAMESPACE = "parser"
PARSER_KIND = "Parser"

class AbcParser(ABC):
    @abstractmethod
    def parse(self, value):
        """ parse a value and return it 

        The parser can
            - leave value unchanged
            - change a value to the one expected
            - raise ValueError exception 
        """
    
class BaseParser(BaseSystem):
    class Config(BaseSystem.Config, extra="forbid"):
        ...

    @staticmethod        
    def __parse__(value:Any, config: Config):
        raise NotImplementedError("__parse__")

    def parse(self, value):
        return self.__parse__(value, self.__config__)

# # ## ## ## ## ## ## ## ## # ## ## ## ## ## ### ## ## ## ## ## ## ## ## # ## ## ###
ParserVar = TypeVar('ParserVar')

class ParserFactory(BaseFactory, Generic[ParserVar]):
    type: Union[str,Callable, Type[AbcParser],List[Union[str,Callable,Type[AbcParser]]]]
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
        return parser( self.type, **self.dict( exclude=set(['type'])) ) 
    
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
        if not field.sub_fields:
            return ParserFactory(v)




class _CombinedParser(BaseParser):
    """ Auto built parser class from several parser classes """
    @classmethod
    def __get_parsers__(cls):
        return tuple()
    
    @classmethod
    def __parse__(cls, value, config):
        for f in cls.__get_parsers__():
            value = f(value, config)
        return value 

class _CallableParser(AbcParser):
    def __init__(self, func: Callable):
        self._func = func
        self.__config__ = BaseParser.Config()
    def parse(self, value):
        return self._func(value)

class _WrapedCallableParser(BaseSystem, AbcParser):
    def parse(self, value):
        raise NotImplementedError('parse')






def _callable_to_fparse(func):
    """ convert a callable function with one argument to __parse__ compatible argument """
    def __parse__(value, _):
        return func(value)
    return __parse__

_parser_counter = int(0)
def _auto_name(obj):
    global _parser_counter
    _parser_counter +=1
    return f"Parser{_parser_counter:03d}"


def _combine_config_class(lst: list, name) -> Type:
    subclasses = []
    for obj in lst:
        if isinstance(obj, str):
            Factory = get_parser_factory_class(obj)
            obj = Factory.get_system_class()

        if isinstance( obj, type):
            try:
                Config = obj.Config
            except AttributeError:
                continue
            subclasses.append( Config)
    subclasses = subclasses or [_CombinedParser.Config]
    return type(name+"Config", tuple(subclasses), {})

def _parser_class_from_list( lst, name):
    fparses = []
    for obj in lst:
        if isinstance(obj, str):
            Factory = get_parser_factory_class(obj)
            obj = Factory.get_system_class()

        if isinstance(obj, type):
            if hasattr(obj, "__parse__"):
                fparses.append( obj.__parse__)
            elif hasattr(obj, "parse"):
                fparses.append( _callable_to_fparse(obj.parse) )
            elif hasattr(obj, "__call__"):
                fparses.append( _callable_to_fparse(obj) )
        elif hasattr(obj, "parse"):
            fparses.append( _callable_to_fparse(obj.parse) )   
        else:
            raise ValueError(f"bad argument for parser_class {obj!r}")
    fparses = tuple(fparses)
    def __get_parsers__(cls):
        return fparses
    Config = _combine_config_class(lst, name)
    return systemclass(type( name, (_CombinedParser, ), {"__get_parsers__":classmethod(__get_parsers__), "Config":Config}))
        


# _parser_factory_loockup = {}
# """ Dictionary containing all target """

# def register_parser_factory(name, cls=None):
#     """ Record a parser with its name 
    
#     Usage:
#         @register_parser(name) 
#         class MyParser(BaseParser):
#             ...

#         Or 

#         register_parser(name, MyParser)

#     """
#     if isinstance(name, type) and cls is None:
#         name, cls = name.__name__, name
           
#     def parser_recorder(icls):
#         if issubclass(icls, BaseParser):
#             fcls = icls.Config
#         else:
#             fcls = icls 
#         if not hasattr(fcls, "build"):
#             raise ValueError("Factory must have a `build` method")
#         _parser_factory_loockup[name] = fcls
#         return icls
    
#     if cls:
#         return parser_recorder(cls)
#     else:
#         return parser_recorder
        

# def get_parser_factory(name):
#     try:
#         return _parser_factory_loockup[name]
#     except KeyError:
#         raise ValueError(f"Unknown parser {name!r}")


def register_parser_factory(name, cls=None) -> None:
    return register_factory(name, cls, kind=PARSER_KIND)

def get_parser_factory_class(name) -> BaseFactory:
    return get_factory_class(name, kind=PARSER_KIND)

def parser_class(
            obj: Union[Callable, Type[AbcParser], str, Iterable[Union[Callable, Type[AbcParser], str]] ], 
            name: str = None
        ) -> Type[AbcParser]:
    """ Build a new parser class for various inputs types 

    Args:
        obj: can be
            - a callable  (e.g. int ) 
            - a parser object: an object with the ``parse`` method  
            - a :class:`BaseParser` (which is returned as is if name is None)  
            - an iterable of a mix of above object kind
        name (str, optional): is the new class name. If not given one is created.  
    """
    if isinstance(obj, str):
        Factory = get_parser_factory_class(obj)
        obj = Factory.get_system_class()
         
    if isinstance( obj, type) and hasattr(obj, "parse"):
        if name is None:
            return obj 
        return type( name, (obj,),  {})

    if name is None:
        name = _auto_name(obj)
    
    
    if hasattr(obj, "__call__"):
        return (type(name , (_WrapedCallableParser, ), {"parse": staticmethod(obj)}))

    
    if hasattr(obj, 'parse'):
        return (type(name , (_WrapedCallableParser, ), {"parse": staticmethod(obj.parse)}))

    if hasattr(obj, "__iter__"):
        return  _parser_class_from_list(obj, name)

    raise ValueError("Bad Argument for parser_class")


def parser_factory_class(obj, name=None):
    Parser = parser_class(obj, name)
    def build(self, parent=None, name=""):
        path = self._make_new_path(parent, name)
        return Parser( __config__= self, __path__=path)
    return type( Parser.__name__+"Factory", (Parser.Config,), {"build": build})

def parser_factory(obj, **kwargs):
    return parser_factory_class(obj)(**kwargs)

def parser(obj, **kwargs):
    if isinstance(obj, type) and hasattr(obj, "parse"):
        return obj(**kwargs)

    if hasattr(obj, "__call__"):
        if kwargs:
            raise ValueError("parser from a callable does not accept kwargs")
        return _CallableParser(obj)
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




