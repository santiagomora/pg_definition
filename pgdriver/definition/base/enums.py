from typing import\
    Any,\
    Optional
from enum import\
    EnumMeta,\
    StrEnum
from .common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowNode,\
    DefinitionFlowBuilder,\
    FlowEndException,\
    FlowNodeException,\
    execute_definition_flow
from .common.node import\
    CommonValidateSingleInheritedClassNode,\
    CommonDetermineIfTargetIsDomainNode


_pg_enum_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('enum-definition-flow')
enum_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_pg_enum_definition_flow_root)


class pg_enum_builtin(EnumMeta):
    def __new__(
        cls, clsname: str, clsbases: tuple[type],
        clsdict: dict[str, Any], **kwargs
    ) -> type:
        try:
            if clsbases[0] != pg_enum:
                # the class is a domain
                for member in clsbases[0]:
                    clsdict[member.name] = member.value
        except NameError:
            pass
        ret_type: type = super()\
            .__new__(cls, clsname, clsbases, clsdict)
        execute_definition_flow(ret_type, _pg_enum_definition_flow_root)
        return ret_type

    @staticmethod
    def _check_for_existing_members_(cls, bases):
        pass


class pg_enum(StrEnum, metaclass=pg_enum_builtin):
    pass


class _EnumValidateSingleInheritedClassNode(CommonValidateSingleInheritedClassNode):
    def __init__(self):
        super().__init__('enum-validate-single-inherited-class-node')


class _EnumDetermineIfTargetIsDomainNode(CommonDetermineIfTargetIsDomainNode):
    def __init__(self):
        super().__init__('enum-determine-if-target-is-domain-node',
                         pg_enum)

    def get_next(self, accumulator: FlowAccumulator) -> DefinitionFlowNode:
        try:
            if self.is_domain:
                return self._nodes['enum-domain-validate-members-node']
            return self._nodes['enum-validate-members-node']
        except KeyError as e:
            raise FlowEndException(f'Choice not found in node {self.name}: {str(e)}')


class _EnumValidateMembersNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('enum-validate-members-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        if target._member_names_ == []:
            raise FlowNodeException(self.name, [f'{target} enum must define own members if it inherits from {pg_enum}'])


class _EnumExtractMembersNode(SingleChoiceDefinitionFlowNode):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self):
        super().__init__('enum-extract-members-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        members: dict[str, str] = {}
        for member in target:
            members[member.name] = member.value
        accumulator.add_definition('members', members)

    def get_dependencies(self) -> tuple[str]:
        return ('enum-validate-members-node',
                'enum-validate-single-inherited-class-node', )


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
        for member in target:
            if member.name not in target_base._member_names_:
                errors.append(f'{target} enum cant define own member {member.name} if it inherits from a {pg_enum} subclass')
        if len(errors) > 0:
            raise FlowNodeException(self.name, errors)


class _EnumDomainStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('enum-domain-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Optional[str]] = dict()
        definition['type'] = target
        definition['base_type'] = target.__bases__[0]
        definition['comment'] = None
        definition['default_value'] = None
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('enum-domain-validate-members-node',
                'enum-validate-single-inherited-class-node', )


enum_flow_builder\
    .at_work_path('validation')\
        .add_node(_EnumValidateSingleInheritedClassNode)\
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

__all__ = {'pg_enum': pg_enum}

