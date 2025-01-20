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
import base_types as bt


__all__ = ['enum']


_enum_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('enum-definition-flow')
enum_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_enum_definition_flow_root)


class enum(bt.enum):
    def __new__(
        cls, clsname: str, clsbases: tuple[type], clsdict: dict[str, Any], *,
        default: Optional[bt.literal] = None
    ) -> type:
        rettype: type = super().__new__(
            cls, clsname, clsbases, clsdict,
            default=default
        )
        execute_definition_flow(rettype, _enum_definition_flow_root)
        return rettype


class _EnumDetermineIfTargetIsDomainNode(CommonDetermineIfTargetIsDomainNode):
    def __init__(self):
        super().__init__('enum-determine-if-target-is-domain-node')

    def get_next(self, accumulator: FlowAccumulator) -> DefinitionFlowNode:
        try:
            if self.is_domain:
                return self._nodes['enum-domain-validate-members-node']
            return self._nodes['enum-validate-members-node']
        except KeyError as e:
            raise FlowException(f'Choice not found in node {self.name}: {str(e)}')


class _EnumValidateMembersNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('enum-validate-members-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # if len(target.__members__.values()) == 0:
            # raise NodeException(self.name, [f'{target} enum must define own members if it inherits from {enum}'])
        if target.__default__() is not None:
            raise NodeException(self.name, [f'{target} enum cant define default values'])


class _EnumExtractMembersNode(SingleChoiceDefinitionFlowNode):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self):
        super().__init__('enum-extract-members-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        members: dict[str, str] = {}
        for name in target.__members__.values():
            members[name] = name
        accumulator.add_definition('members', members)

    def get_dependencies(self) -> tuple[str]:
        return ('enum-validate-members-node', )


class _EnumStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

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


class _EnumDomainValidateMembersNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('enum-domain-validate-members-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        target_base: type = target.__bases__[0]
        errors: list[str] = []
        for member in target.__members__.values():
            print( member.name not in target_base.__members__)
            if member.name not in target_base.__members__:
                errors.append(f'{target} enum cant define own member {member.name} if it inherits from a {enum} subclass')
        if len(errors) > 0:
            raise NodeException(self.name, errors)


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
        definition['default'] = target.__default__()
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('enum-domain-validate-members-node', )


enum_flow_builder\
    .at_work_path('validation')\
        .add_node(_EnumDetermineIfTargetIsDomainNode)\
        .build_choice(_EnumValidateMembersNode)\
            .at_work_path('extraction')\
            .add_node(_EnumExtractMembersNode)\
            .at_work_path('')\
            .add_node(_EnumStoreFinalDefinitionNode)\
            .end_choice()\
        .build_choice(_EnumDomainValidateMembersNode)\
            .at_work_path('')\
            .add_node(_EnumDomainStoreFinalDefinitionNode).critical()\
            .end_choice()

