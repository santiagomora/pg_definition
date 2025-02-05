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
from ..objects.comment import\
    add_comment
from ..common.inspection import\
    check_tp_is_domain,\
    check_tp_is_not_domain
from pydantic_core import\
    core_schema
from pydantic import\
    GetCoreSchemaHandler


__all__ = ['builtin', 'compound']


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
    class set_constraint(bt.compound.set_constraint):
        def __init__(
            self, *, field_name: str, constraint: bt.LogicOperand, accessor: str
        ) -> None:
            self.accessor = accessor
            return super().__init__(field_name=field_name, constraint=constraint)

        def __call__(self, target: type) -> type:
            self._constraint.name = f'{target.__name__}_{self._constraint.name}'
            target._postgres_definition[self.accessor][self._field_name]['check'] = self._constraint
            return super().__call__(target)

    class set_default(bt.compound.set_default):
        pass


class builtin(bt.builtin):
    class set_default(bt.builtin.set_default):
        def __call__(self, target: type) -> type:
            check_tp_is_domain(target)
            target._postgres_definition['default'] = self._default
            return super().__call__(target)

    class set_check_constraint(bt.builtin.set_constraint):
        def __init__(self, *, name: str, constraint: bt.LogicOperand) -> None:
            constraint.name = name
            return super().__init__(constraint)

        def __call__(self, target: type) -> type:
            check_tp_is_domain(target)
            target._postgres_definition['check'] = self._constraint
            return super().__call__(target)

    class add_comment(add_comment):
        def __call__(self, target: type) -> type:
            check_tp_is_domain(target)
            return super().__call__(target)

    def __new__(
        cls, clsname: str, clsbases: tuple[type],
        clsdict: dict[str, Any]
    ) -> type:
        rettype: type = super().__new__(
            cls, clsname, clsbases, clsdict
        )
        execute_definition_flow(rettype, _builtin_definition_flow_root)
        return rettype

    def definition_context(self) -> type[bt.OperandDefinitionContext]:
        return BuiltinDomainOperandDefinitionContext


class _BuiltinDetermineIfTargetIsDomainNode(MultipleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__(2, 'builtin-determine-if-target-is-domain-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        self.is_domain = hasattr(target, 'base_type')\
            and not target.base_type.qualified_name.startswith('base_types')

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
        definition['check'] = None
        definition['default'] = bt.Undefined
        accumulator.add_definition('final', definition)


builtin_builder\
    .at_work_path('')\
    .add_node(_BuiltinDetermineIfTargetIsDomainNode).critical()\
    .build_choice(_BuiltinDomainStoreFinalDefinitionNode)\
        .end_choice()\
    .build_choice(_BuiltinStoreFinalDefinition)\
        .end_choice()
