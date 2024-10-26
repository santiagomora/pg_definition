from typing import\
    Any
from pydantic_core import\
    core_schema,\
    SchemaValidator
from pydantic import\
    GetCoreSchemaHandler
from datetime import\
    datetime,\
    time,\
    date
from .common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    DefinitionFlowBuilder,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowNode,\
    FlowNodeException,\
    MultipleChoiceDefinitionFlowNode,\
    execute_definition_flow
from typing import \
    Optional
from .common.node import\
    CommonValidateSingleInheritedClassNode


# TODO configure flow components runtime dependencies
_pg_builtin_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('builtin-definition-flow')
builtin_builder = DefinitionFlowBuilder(_pg_builtin_definition_flow_root)


class pg_builtin(type):
    def __new__(cls, clsname: str, clsbases: tuple[type],
                clsdict: dict[str, Any], **kwargs) -> type:

        def __repr__(self):
            return f'{clsname}({clsbases[0].__repr__(self)})'

        def __new__(cls, *args, **kwargs) -> Any:
            if hasattr(cls, '__pg_definition'):
                validator: SchemaValidator = SchemaValidator(cls.__get_pydantic_core_schema__(None, None))
                validator.validate_python(*args)
                definition = getattr(cls, '__pg_definition')()
                if definition['check'] is not None:
                    definition['check']._validate(*args, **kwargs)
            return clsbases[0].__new__(clsbases[0], *args, **kwargs)

        # we execute the definition flow on the builtin type as well
        ret_type: type = super()\
            .__new__(cls, clsname, clsbases,
                     clsdict | {'__new__': __new__,
                                '__repr__': __repr__})
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


class pg_int(int, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.int_schema(strict=True, le=0x7fffffff, ge=-0x7fffffff)


class pg_bigint(int, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.int_schema(strict=True)


class pg_smallint(int, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.int_schema(strict=True, le=0x7fff, ge=-0x7fff)


class pg_text(str, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.str_schema(strict=True)


class pg_float(float, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.float_schema(strict=True)


class pg_double(float, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.float_schema(strict=True)


class pg_bytea(bytes, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.bytes_schema(strict=True)


class pg_timestamp(datetime, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.datetime_schema(strict=True, tz_constraint='naive')


class pg_timestamptz(datetime, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.datetime_schema(strict=True, tz_constraint='aware')


class pg_time(time, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.time_schema(strict=True, tz_constraint='naive')


class pg_timetz(time, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.time_schema(strict=True, tz_constraint='aware')


class pg_date(date, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.date_schema(strict=True)


class pg_boolean(int, metaclass=pg_builtin):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.int_schema(strict=True, ge=0, le=1)


__all__ = {
    'pg_int':                pg_int,
    'pg_bigint':             pg_bigint,
    'pg_smallint':           pg_smallint,
    'pg_text':               pg_text,
    'pg_double':             pg_double,
    'pg_float':              pg_float,
    'pg_bytea':              pg_bytea,
    'pg_timestamp':          pg_timestamp,
    'pg_timestamptz':        pg_timestamptz,
    'pg_time':               pg_time,
    'pg_timetz':             pg_timetz,
    'pg_date':               pg_date,
    'pg_boolean':            pg_boolean}

