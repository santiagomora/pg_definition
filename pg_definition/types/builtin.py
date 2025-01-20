from typing import\
    Any,\
    Union,\
    TypeAlias
from ..common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    DefinitionFlowBuilder,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowNode,\
    MultipleChoiceDefinitionFlowNode,\
    execute_definition_flow
from typing import \
    Optional
import base_types as bt
from ..objects.check import\
    check


__all__ = ['builtin']


_builtin_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('builtin-definition-flow')
builtin_builder = DefinitionFlowBuilder(_builtin_definition_flow_root)


class BuiltinDomainOperandDefinitionContext(bt.OperandDefinitionContext):
    @classmethod
    def parse_field(cls, field_instance: bt.field) -> str:
        # illegal
        raise NotImplementedError

    @classmethod
    def parse_this(cls, this_instance: bt.this) -> str:
        return 'VALUE'


class compound(bt.compound):
    pass


class builtin(bt.builtin):
    def __new__(
        cls, clsname: str, clsbases: tuple[type],
        clsdict: dict[str, Any], *, check_predicate: Optional[check] = None,
        default: Optional[bt.literal] = None
    ) -> type:
        rettype: type = super().__new__(
            cls, clsname, clsbases, clsdict,
            check_predicate=None if check_predicate is None else check_predicate.predicate, default=default
        )
        execute_definition_flow(rettype, _builtin_definition_flow_root)
        return rettype

    def definition_context(self) -> type[bt.OperandDefinitionContext]:
        return BuiltinDomainOperandDefinitionContext


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
        definition['schema'] = None
        definition['kind'] = 'builtin'
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ()


class _BuiltinDomainStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('builtin-domain-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Optional[str]] = dict()
        definition['schema'] = None
        definition['type'] = target
        definition['base_type'] = target.__bases__[0]
        definition['comment'] = None
        definition['kind'] = 'domain'
        predicate = getattr(target, '__check_predicate__')()
        definition['check'] = predicate.parent if predicate is not None else None
        definition['default'] = getattr(target, '__default__')()
        accumulator.add_definition('final', definition)


builtin_builder\
    .at_work_path('')\
        .add_node(_BuiltinDetermineIfTargetIsDomainNode).critical()\
    .build_choice(_BuiltinDomainStoreFinalDefinitionNode)\
        .end_choice()\
    .build_choice(_BuiltinStoreFinalDefinition)\
        .end_choice()


class int2(bt.int2, metaclass=builtin):
    pass


class int4(bt.int4, metaclass=builtin):
    pass


class int8(bt.int8, metaclass=builtin):
    pass


class float4(bt.float4, metaclass=builtin):
    pass


class float8(bt.float8, metaclass=builtin):
    pass


class int1(bt.int1, metaclass=builtin):
    pass


class bool(bt.bool, metaclass=builtin):
    pass


class text(bt.text, metaclass=builtin):
    pass


class timestamptz(bt.timestamptz, metaclass=builtin):
    pass


class date(bt.date, metaclass=builtin):
    pass
