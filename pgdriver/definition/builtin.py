from typing import\
    Any,\
    Union
from pydantic_core import\
    core_schema
from pydantic import\
    GetCoreSchemaHandler
from .common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    DefinitionFlowBuilder,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowNode,\
    MultipleChoiceDefinitionFlowNode,\
    execute_definition_flow
from typing import \
    Optional
import numpy as np
from datetime import\
    datetime,\
    date as _date,\
    time


# TODO configure flow components runtime dependencies
_builtin_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('builtin-definition-flow')
builtin_builder = DefinitionFlowBuilder(_builtin_definition_flow_root)


__all__ = ['integer', 'bigint', 'smallint', 'text', 'double', 'real', 'byte', 'char', 'timestamptz', 'timetz', 'date', 'boolean', 'builtin_instance']


class builtin(type):
    def __new__(cls, clsname: str, clsbases: tuple[type],
                clsdict: dict[str, Any], **kwargs) -> type:

        if len(clsbases) > 1:
            raise TypeError(f'Class {cls} doesnt allow multiple bases')

        def __new__(cls_, *args, **kwargs) -> Any:
            instance = clsbases[0].__new__(cls_, *args, **kwargs)
            if hasattr(clsbases[0], '__pg_validate_instance__'):
                instance = clsbases[0].__pg_validate_instance__(instance)
            return cls_.__pg_validate_instance__(instance)

        @classmethod
        def __pg_validate_instance__(cls, instance):
            if hasattr(cls, '__pg_definition'):
                definition = getattr(cls, '__pg_definition')()
                if 'check' in definition and definition['check'] is not None:
                    instance = definition['check']._validate(instance)
            return instance

        @classmethod
        def __pg_attempt_to_create_instance__(cls, value, validation_info):
            if value is None:
                definition = getattr(cls, '__pg_definition')()
                default_value = getattr(definition, 'default_value', None)
                return value if default_value is None else default_value
            creation_method = getattr(cls, '__pg_create_instance_custom__', cls.__pg_create_instance__)
            return creation_method(value)

        @classmethod
        def __pg_create_instance__(cls, value):
            return value if isinstance(value, cls) else cls(value)

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type,
            handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            return core_schema.with_info_plain_validator_function(
                function=cls.__pg_attempt_to_create_instance__)

        def __repr__(self):
            return str(self)

        rettype: type = super()\
            .__new__(cls, clsname, clsbases,
                     {'__new__': __new__,
                      '__repr__': __repr__,
                      '__pg_validator': None,
                      '__get_pydantic_core_schema__': __get_pydantic_core_schema__,
                      '__pg_attempt_to_create_instance__': __pg_attempt_to_create_instance__,
                      '__pg_create_instance__': __pg_create_instance__,
                      '__pg_validate_instance__': __pg_validate_instance__} | clsdict)
        execute_definition_flow(rettype, _builtin_definition_flow_root)
        return rettype


class _BuiltinDetermineIfTargetIsDomainNode(MultipleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__(2, 'builtin-determine-if-target-is-domain-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        self.is_domain = hasattr(target.__bases__[0], '__pg_definition')

    def get_next(self, accumulator: FlowAccumulator) -> DefinitionFlowNode:
        if self.is_domain:
            return self._nodes['builtin-domain-store-final-definition-node']
        return self._nodes['builtin-store-final-definition-node']


class _BuiltinStoreFinalDefinition(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('builtin-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, str] = dict()
        definition['type'] = target
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ()


class _BuiltinDomainStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('builtin-domain-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Optional[str]] = dict()
        definition['type'] = target
        definition['base_type'] = target.__bases__[0]
        definition['comment'] = None
        definition['check'] = accumulator.get_definition('check', 'extraction')
        definition['default_value'] = None
        accumulator.add_definition('final', definition)


builtin_builder\
    .at_work_path('')\
        .add_node(_BuiltinDetermineIfTargetIsDomainNode).critical()\
    .build_choice(_BuiltinDomainStoreFinalDefinitionNode)\
        .end_choice()\
    .build_choice(_BuiltinStoreFinalDefinition)\
        .end_choice()


class smallint(np.int16, metaclass=builtin):
    pass


class integer(np.int32, metaclass=builtin):
    pass


class bigint(np.int64, metaclass=builtin):
    pass


class text(str, metaclass=builtin):
    pass


class real(np.float32, metaclass=builtin):
    pass


class double(np.float64, metaclass=builtin):
    pass


class char(np.int8, metaclass=builtin):
    pass


class byte(np.byte, metaclass=builtin):
    pass


class boolean(np.bool, metaclass=builtin):
    pass


def _create_from_model_field(cls: type, value: Any):
    if isinstance(value, cls):
        return value
    elif isinstance(value, str):
        return cls.fromisoformat(value)
    raise ValueError(f'Invalid value for {cls.__name__}')


# we'll always work with ISO8061 utc timestamptzs, what will change is
# how these representations get stored into the database, we will
# have to define each function for conversion
class timestamptz(datetime, metaclass=builtin):
    def __new__(
        cls, *args, **kwargs
    ):
        if isinstance(args[0], str):
            t: timestamptz = cls.fromisoformat(args[0])
            args = (t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond)
        return super().__new__(cls, *args, **kwargs)


class timetz(time, metaclass=builtin):
    # timetz will always be a tuple, as it is possible to specify timetz units
    # first parameter can be a 'hh?:mm?:ss?,(...)' string or an integer
    def __new__(
        cls, *args, **kwargs
    ):
        if isinstance(args[0], str):
            t: timetz = cls.fromisoformat(args[0])
            args = (t.hour, t.minute, t.second, t.microsecond)
        return super().__new__(cls, *args, **kwargs)


class date(_date, metaclass=builtin):
    def __new__(
        cls, *args, **kwargs
    ):
        if isinstance(args[0], str):
            d: date = cls.fromisoformat(args[0])
            args = (d.year, d.month, d.day)
        return super().__new__(cls, *args, **kwargs)


builtin_instance = Union[integer, bigint, smallint, text, double, real, byte, char, timestamptz, timetz, date, boolean]
