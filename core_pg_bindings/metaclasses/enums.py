from typing import\
    Any,\
    Optional
from ..common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowNode,\
    DefinitionFlowBuilder,\
    FlowException,\
    NodeException,\
    execute_definition_flow
from ..common.node import\
    CommonDetermineIfTargetIsDomainNode
import core_types as bt
from ..common.inspection import\
    check_tp_is_domain
from ..objects.comment import\
    add_comment


__all__ = ['enum']


_enum_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('enum-definition-flow')
enum_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_enum_definition_flow_root)


class enum(bt.enum):
    class set_default(bt.enum.set_default):
        def __call__(self, target: type) -> type:
            check_tp_is_domain(target)
            assert target._postgres_definition['default'] is bt.Undefined
            target._postgres_definition['default'] = self._default
            return super().__call__(target)

    class add_comment(add_comment):
        pass

    def __new__(
        cls, clsname: str, clsbases: tuple[type], clsdict: dict[str, Any]
    ) -> type:
        rettype: type = super().__new__(
            cls, clsname, clsbases, clsdict
        )
        execute_definition_flow(rettype, _enum_definition_flow_root)
        return rettype


class _EnumDetermineIfTargetIsDomainNode(CommonDetermineIfTargetIsDomainNode):
    def __init__(self):
        super().__init__('enum-determine-if-target-is-domain-node')

    def get_next(self, accumulator: FlowAccumulator) -> DefinitionFlowNode:
        try:
            if self.is_domain:
                return self._nodes['enum-domain-store-final-definition-node']
            return self._nodes['enum-extract-members-node']
        except KeyError as e:
            raise FlowException(f'Choice not found in node {self.name}: {str(e)}')


class _EnumExtractMembersNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('enum-extract-members-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        members: dict[str, str] = {}
        for name in target.enum.__members__.values():
            members[name] = name
        accumulator.add_definition('members', members)


class _EnumStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('enum-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Optional[str]] = dict()
        definition['type'] = target
        definition['comment'] = None
        definition['schema'] = None
        definition['kind'] = 'enum'
        definition['members'] = accumulator.get_definition('members', 'extraction')
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('enum-extract-members-node', )


class _EnumDomainStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('enum-domain-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Optional[str]] = dict()
        definition['schema'] = None
        definition['type'] = target
        definition['base_type'] = target.__bases__[0]
        definition['comment'] = None
        definition['kind'] = 'domain'
        definition['default'] = target._pydantic_adapt.default
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('enum-domain-validate-members-node', )


enum_flow_builder\
    .add_node(_EnumDetermineIfTargetIsDomainNode)\
    .at_work_path('extraction')\
    .build_choice(_EnumExtractMembersNode)\
        .at_work_path('')\
        .add_node(_EnumStoreFinalDefinitionNode)\
        .end_choice()\
    .at_work_path('')\
    .build_choice(_EnumDomainStoreFinalDefinitionNode)\
        .end_choice()

