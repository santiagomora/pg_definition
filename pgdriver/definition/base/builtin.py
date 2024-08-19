from typing import\
    Any,\
    Optional
from pydantic_core import\
    core_schema,\
    SchemaValidator
from pydantic import\
    GetCoreSchemaHandler
from datetime import\
    datetime,\
    time,\
    date
from .common.meta import\
    pg_type_check
from .common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    DefinitionFlowNodeFactory,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowNode,\
    FlowNodeException,\
    MultipleChoiceDefinitionFlowNode,\
    execute_definition_flow
from .common.node import\
    CommonValidateSingleInheritedClassNode
from .domain import\
    DomainExtractCheckConstraintNode,\
    DomainExtractCommentNode,\
    DomainMergeCheckConstraintNode,\
    DomainStoreFinalDefinitionNode


_pg_builtin_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('builtin-definition-flow')


class pg_builtin(type):
    def __new__(cls, clsname: str, clsbases: tuple[type],
                clsdict: dict[str, Any]) -> type:
        @classmethod
        def __init_subclass__(cls, *args, **kwargs):
            super(type, cls).__init_subclass__(*args, **kwargs)
            setattr(cls, '__pg_is_builtin_domain', True)

        def __repr__(self):
            return f'{clsname}({clsbases[0].__repr__(self)})'

        # we execute the definition flow on the builtin type as well
        ret_type: type = super().__new__(cls, clsname, clsbases,
                                         clsdict | {'__init_subclass__': __init_subclass__,
                                                    '__repr__': __repr__})
        execute_definition_flow(ret_type, _pg_builtin_definition_flow_root)
        return ret_type


class _BuiltinValidateSingleInheritedClassNode(CommonValidateSingleInheritedClassNode):
    def __init__(self):
        super().__init__('builtin-validate-single-inherited-class-node')


class _BuiltinDomainValidateCheckConstraintNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('builtin-domain-validate-check-constraint-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        try:
            if not hasattr(target, f'_{target.__name__}__pg_check'):
                return
            check: pg_type_check = getattr(target, f'_{target.__name__}__pg_check')
            check.check_valid_constraint_definition(target)
        except TypeError as e:
            raise FlowNodeException(self.name, [str(e)])


class _BuiltinExtractTypeNameNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('builtin-extract-type-name-node')

    def execute(self, on_type: type, accumulator: FlowAccumulator) -> None:
        accumulator.add_definition('type_name',
                                   on_type.__name__.replace('pg_', ''))


class _BuiltinDetermineIfTargetIsDomainNode(MultipleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__(2, 'builtin-determine-if-target-is-domain-node')

    def execute(self, on_type: type, accumulator: FlowAccumulator) -> None:
        self.is_domain = getattr(on_type, '__pg_is_builtin_domain', False)

    def get_next(self, accumulator: FlowAccumulator) -> DefinitionFlowNode:
        if self.is_domain:
            return self._nodes['builtin-domain-validate-check-constraint-definition-node']
        return self._nodes['builtin-store-final-definition-node']


class _BuiltinStoreFinalDefinition(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('builtin-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, str] = dict()
        definition['schema_name'] = 'public'
        definition['type_name'] = accumulator.get_definition('type_name', 'extraction')
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('builtin-extract-type-name-node', )


class _BuiltinDomainExtractCheckConstraintNode(DomainExtractCheckConstraintNode):
    def __init__(self):
        super().__init__('builtin-domain-extract-check-constraint-node')


class _BuiltinDomainExtractCommentNode(DomainExtractCommentNode):
    def __init__(self):
        super().__init__('builtin-domain-extract-comment-node')


class _BuiltinDomainMergeCheckConstraintNode(DomainMergeCheckConstraintNode):
    def __init__(self):
        super().__init__('builtin-domain-merge-check-constraint-node')


class _BuiltinDomainStoreFinalDefinitionNode(DomainStoreFinalDefinitionNode):
    def __init__(self):
        super().__init__('builtin-domain-store-final-definition-node')


_builtin_node_factory: DefinitionFlowNodeFactory = DefinitionFlowNodeFactory()

# build the domain definition flow
_domain_flow_first_node: Optional[DefinitionFlowNode] = None
_domain_flow_last_node: Optional[DefinitionFlowNode] = None
_pg_domain_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('pgdriver-domain-definition-flow')

with _builtin_node_factory.at_work_path('validation') as fact:
    _domain_flow_first_node = _domain_flow_last_node \
        = fact.get_definition_node(_BuiltinDomainValidateCheckConstraintNode)

with _builtin_node_factory.at_work_path('extraction') as fact:
    _domain_flow_last_node = _domain_flow_last_node \
        .set_next(fact.get_definition_node(_BuiltinDomainExtractCheckConstraintNode).critical())\
        .set_next(fact.get_definition_node(_BuiltinDomainExtractCommentNode))

with _builtin_node_factory.at_work_path('merge') as fact:
    _domain_flow_last_node = _domain_flow_last_node\
        .set_next(fact.get_definition_node(_BuiltinDomainMergeCheckConstraintNode))

with _builtin_node_factory.at_work_path('') as fact:
    _domain_flow_last_node = _domain_flow_last_node\
        .set_next(fact.get_definition_node(_BuiltinDomainStoreFinalDefinitionNode))


# build the builtin definition flow
_builtin_flow_last_node: Optional[DefinitionFlowNode] = None

with _builtin_node_factory.at_work_path('validation') as fact:
    _builtin_flow_last_node = _pg_builtin_definition_flow_root\
        .set_next(fact.get_definition_node(_BuiltinValidateSingleInheritedClassNode))

with _builtin_node_factory.at_work_path('extraction') as fact:
    _builtin_flow_last_node = _builtin_flow_last_node\
        .set_next(fact.get_definition_node(_BuiltinExtractTypeNameNode).critical())

with _builtin_node_factory.at_work_path('') as fact:
    _builtin_flow_last_node = _builtin_flow_last_node\
        .set_next(fact.get_definition_node(_BuiltinDetermineIfTargetIsDomainNode))\
        .set_next(_domain_flow_first_node)\
        .set_next(fact.get_definition_node(_BuiltinStoreFinalDefinition).critical())


def _with_schema_metaclass(schema: core_schema.CoreSchema) -> type[pg_builtin]:
    class _schema_builtin(pg_builtin):
        def __new__(cls, clsname: str, clsbases: tuple[type],
                    clsdict: dict[str, Any]) -> type:
            def __new__(cls, *args, **kwargs) -> Any:
                validator: SchemaValidator = SchemaValidator(schema)
                validator.validate_python(*args)
                if hasattr(cls, f'_{cls.__name__}__pg_check'):
                    getattr(cls, f'_{cls.__name__}__pg_check').validate_value(*args)
                return clsbases[0].__new__(cls, *args, **kwargs)

            @classmethod
            def __get_pydantic_core_schema__(cls, source: type[Any],
                                             handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
                return schema
            return super().__new__(cls, clsname, clsbases,
                                   clsdict | {'__new__': __new__,
                                              '__get_pydantic_core_schema__': __get_pydantic_core_schema__})
    return _schema_builtin


class pg_int(int,
             metaclass=_with_schema_metaclass(core_schema.int_schema(strict=True,
                                                                     le=0x7fffffff,
                                                                     ge=-0x7fffffff))):
    pass


class pg_bigint(int,
                metaclass=_with_schema_metaclass(core_schema.int_schema(strict=True))):
    pass


class pg_smallint(int,
                  metaclass=_with_schema_metaclass(core_schema.int_schema(strict=True,
                                                                          le=0x7fff,
                                                                          ge=-0x7fff))):
    pass


class pg_text(str,
              metaclass=_with_schema_metaclass(core_schema.str_schema(strict=True))):
    pass


class pg_float(float,
               metaclass=_with_schema_metaclass(core_schema.float_schema(strict=True))):
    pass


class pg_double(float,
                metaclass=_with_schema_metaclass(core_schema.float_schema(strict=True))):
    pass


class pg_bytea(bytes,
               metaclass=_with_schema_metaclass(core_schema.bytes_schema(strict=True))):
    pass


class pg_timestamp(datetime,
                   metaclass=_with_schema_metaclass(core_schema.datetime_schema(strict=True,
                                                                                tz_constraint='naive'))):
    pass


class pg_timestamptz(datetime,
                     metaclass=_with_schema_metaclass(core_schema.datetime_schema(strict=True,
                                                                                  tz_constraint='aware'))):
    pass


class pg_time(time,
              metaclass=_with_schema_metaclass(core_schema.time_schema(strict=True,
                                                                       tz_constraint='naive'))):
    pass


class pg_timetz(time,
                metaclass=_with_schema_metaclass(core_schema.time_schema(strict=True,
                                                                         tz_constraint='aware'))):
    pass


class pg_date(date,
              metaclass=_with_schema_metaclass(core_schema.date_schema(strict=True))):
    pass


class pg_boolean(metaclass=_with_schema_metaclass(core_schema.bool_schema(strict=True))):
    pass


__all__ = {
    'pg_int':         pg_int,
    'pg_bigint':      pg_bigint,
    'pg_smallint':    pg_smallint,
    'pg_text':        pg_text,
    'pg_double':      pg_double,
    'pg_float':       pg_float,
    'pg_bytea':       pg_bytea,
    'pg_timestamp':   pg_timestamp,
    'pg_timestamptz': pg_timestamptz,
    'pg_time':        pg_time,
    'pg_timetz':      pg_timetz,
    'pg_date':        pg_date,
    'pg_boolean':     pg_boolean}

