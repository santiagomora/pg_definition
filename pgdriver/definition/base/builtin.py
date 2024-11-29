from typing import\
    Any,\
    Literal
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
from .common.node import\
    CommonValidateSingleInheritedClassNode
import numpy as np
import warnings

# TODO configure flow components runtime dependencies
_pg_builtin_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('builtin-definition-flow')
builtin_builder = DefinitionFlowBuilder(_pg_builtin_definition_flow_root)


class pg_builtin(type):
    def __new__(cls, clsname: str, clsbases: tuple[type],
                clsdict: dict[str, Any], **kwargs) -> type:

        def __new__(cls_, *args, **kwargs) -> Any:
            with warnings.catch_warnings(action="ignore"):
                # catches numpy.datetime64 warning when instancing datetime with timezone
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
            return f'{self.__class__.__name__}({self})'

        ret_type: type = super()\
            .__new__(cls, clsname, clsbases,
                     {'__new__': __new__,
                      '__repr__': __repr__,
                      '__pg_validator': None,
                      '__get_pydantic_core_schema__': __get_pydantic_core_schema__,
                      '__pg_attempt_to_create_instance__': __pg_attempt_to_create_instance__,
                      '__pg_create_instance__': __pg_create_instance__,
                      '__pg_validate_instance__': __pg_validate_instance__} | clsdict)
        execute_definition_flow(ret_type, _pg_builtin_definition_flow_root)
        return ret_type


class _BuiltinValidateSingleInheritedClassNode(CommonValidateSingleInheritedClassNode):
    def __init__(self):
        super().__init__('builtin-validate-single-inherited-class-node')


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
    .at_work_path('validation')\
        .add_node(_BuiltinValidateSingleInheritedClassNode)\
    .at_work_path('')\
        .add_node(_BuiltinDetermineIfTargetIsDomainNode).critical()\
    .build_choice(_BuiltinDomainStoreFinalDefinitionNode)\
        .end_choice()\
    .build_choice(_BuiltinStoreFinalDefinition)\
        .end_choice()


class pg_smallint(np.int16, metaclass=pg_builtin):
    pass


class pg_int(np.int32, metaclass=pg_builtin):
    pass


class pg_bigint(np.int64, metaclass=pg_builtin):
    pass


class pg_text(str, metaclass=pg_builtin):
    pass


class pg_float(np.float32, metaclass=pg_builtin):
    pass


class pg_double(np.float64, metaclass=pg_builtin):
    pass


class pg_char(np.int8, metaclass=pg_builtin):
    pass


class pg_byte(np.byte, metaclass=pg_builtin):
    pass


class pg_boolean(np.bool, metaclass=pg_builtin):
    pass


def _create_from_model_field(cls: type, value: Any, default_unit: str):
    if isinstance(value, cls):
        return value
    elif isinstance(value, tuple):
        return cls(value[0], value[1])
    elif isinstance(value, str):
        return cls(value, default_unit)
    raise ValueError(f'Invalid value for {cls.__name__}')


# we'll always work with ISO8061 utc timestamps, what will change is
# how these representations get stored into the database, we will
# have to define each function for conversion
class pg_datetime(np.datetime64, metaclass=pg_builtin):
    @classmethod
    def __pg_create_instance_custom__(
        cls,
        value: Any
    ):
        return _create_from_model_field(cls, value, 'us')


class pg_time(np.datetime64, metaclass=pg_builtin):
    # pg_time will always be a tuple, as it is possible to specify time units
    # first parameter can be a 'hh?:mm?:ss?,(...)' string or an integer
    def __new__(
        cls,
        value: str | int,
        unit: Literal['h', 'm', 's', 'ms', 'us', 'ns', 'fs', 'as'] = 'us'
    ):
        if unit not in ('h', 'm', 's', 'ms', 'us', 'ns', 'fs', 'as'):
            raise ValueError('Invalid unit for pg_time')
        if isinstance(value, str):
            value = f'1970-01-01T{value}'
        return super().__new__(cls, value, unit)

    @classmethod
    def __pg_create_instance_custom__(
        cls,
        value: Any
    ):
        return _create_from_model_field(cls, value, 'us')


class pg_date(np.datetime64, metaclass=pg_builtin):
    def __new__(
        cls,
        value: str | int
    ):
        return super().__new__(cls, value, 'D')


__all__ = {
    'pg_int':      pg_int,
    'pg_bigint':   pg_bigint,
    'pg_smallint': pg_smallint,
    'pg_text':     pg_text,
    'pg_double':   pg_double,
    'pg_float':    pg_float,
    'pg_byte':     pg_byte,
    'pg_char':     pg_char,
    'pg_datetime': pg_datetime,
    'pg_time':     pg_time,
    'pg_date':     pg_date,
    'pg_boolean':  pg_boolean}
