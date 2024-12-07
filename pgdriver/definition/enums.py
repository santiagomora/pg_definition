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
    FlowException,\
    NodeException,\
    execute_definition_flow
from .common.node import\
    CommonDetermineIfTargetIsDomainNode


_enums_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('enums-definition-flow')
enums_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_enums_definition_flow_root)


class enums_builtin(EnumMeta):
    def __new__(
        cls, clsname: str, clsbases: tuple[type],
        clsdict: dict[str, Any], **kwargs
    ) -> type:
        if len(clsbases) > 1:
            raise TypeError(f'Class {cls} doesnt allow multiple bases')

        try:
            if clsbases[0] != enums:
                # the class is a domain
                for member in clsbases[0]:
                    clsdict[member.name] = member.value
        except NameError:
            pass
        rettype: type = super()\
            .__new__(cls, clsname, clsbases, clsdict)
        execute_definition_flow(rettype, _enums_definition_flow_root)
        return rettype

    @staticmethod
    def _check_for_existing_members_(cls, bases):
        pass


class enums(StrEnum, metaclass=enums_builtin):
    pass


class _EnumDetermineIfTargetIsDomainNode(CommonDetermineIfTargetIsDomainNode):
    def __init__(self):
        super().__init__('enums-determine-if-target-is-domain-node',
                         enums)

    def get_next(self, accumulator: FlowAccumulator) -> DefinitionFlowNode:
        try:
            if self.is_domain:
                return self._nodes['enums-domain-validate-members-node']
            return self._nodes['enums-validate-members-node']
        except KeyError as e:
            raise FlowException(f'Choice not found in node {self.name}: {str(e)}')


class _EnumValidateMembersNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('enums-validate-members-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        if target._member_names_ == []:
            raise NodeException(self.name, [f'{target} enums must define own members if it inherits from {enums}'])


class _EnumExtractMembersNode(SingleChoiceDefinitionFlowNode):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self):
        super().__init__('enums-extract-members-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        members: dict[str, str] = {}
        for member in target:
            members[member.name] = member.value
        accumulator.add_definition('members', members)

    def get_dependencies(self) -> tuple[str]:
        return ('enums-validate-members-node', )


class _EnumStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('enums-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Optional[str]] = dict()
        definition['type'] = target
        definition['comment'] = None
        definition['members'] = accumulator.get_definition('members', 'extraction')
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('enums-extract-members-node', )


class _EnumDomainValidateMembersNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('enums-domain-validate-members-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        target_base: type = target.__bases__[0]
        errors: list[str] = []
        for member in target:
            if member.name not in target_base._member_names_:
                errors.append(f'{target} enums cant define own member {member.name} if it inherits from a {enums} subclass')
        if len(errors) > 0:
            raise NodeException(self.name, errors)


class _EnumDomainStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('enums-domain-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Optional[str]] = dict()
        definition['type'] = target
        definition['base_type'] = target.__bases__[0]
        definition['comment'] = None
        definition['default_value'] = None
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('enums-domain-validate-members-node', )


enums_flow_builder\
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

__all__ = {'enums': enums}

