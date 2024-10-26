from typing import\
    Any
from enum import\
    Enum
from .common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowNode,\
    DefinitionFlowBuilder,\
    FlowEndException
from .common.node import\
    CommonValidateSingleInheritedClassNode,\
    CommonDetermineIfTargetIsDomainNode


_pg_enum_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('enum-definition-flow')
enum_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_pg_enum_definition_flow_root)


class pg_enum(metaclass=Enum):
    def __init_subclass__(cls, *args, **kwargs):
        Enum.__init_subclass__(cls, *args, **kwargs)
        accumulator: FlowAccumulator = FlowAccumulator(cls)
        _pg_enum_definition_flow_root.execute(cls, accumulator)


class _EnumValidateSingleInheritedClassNode(CommonValidateSingleInheritedClassNode):
    def __init__(self):
        super().__init__('enum-validate-single-inherited-class-node')


class _EnumDependsOnValidationNodes:
    def get_dependencies(self) -> tuple[str]:
        return ('enum-validate-single-inherited-class-node', )


class _EnumDetermineIfTargetIsDomainNode(CommonDetermineIfTargetIsDomainNode):
    def __init__(self):
        super().__init__('enum-determine-if-target-is-domain-node',
                         pg_enum)

    def get_next(self,
                 accumulator: FlowAccumulator) -> DefinitionFlowNode:
        try:
            if self.is_domain:
                return self._nodes['enum-store-comment-definition-node']
            return self._nodes['enum-store-values-node']
        except KeyError as e:
            raise FlowEndException(f'Choice not found in node {self.name}: {str(e)}')


class _EnumExtractValuesNode(SingleChoiceDefinitionFlowNode,
                             _EnumDependsOnValidationNodes):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self):
        super().__init__('enum-extract-values-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        pass
        # for value in list(target):
        # indexes: list[dict[str, Any]] = [ix for ix in extract_by_instance_type_from_model_fields_info(
        #     target,
        #     pg_meta.index,
        #     self._base_class,
        #     lambda field_name, index: {
        #         'column_name': field_name,
        #         'type':   index.type,
        #         'name':   index.name,
        #         'is_unique': False})]
        # try:
        #     grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
        #         ('name', ),
        #         indexes)
        #     definition: list[dict[str, Any]] = [aggregate(grouped_by_name[ix_name], {
        #             'column_name': ordered_set_accumulator}) for ix_name in grouped_by_name]
        #     if len(definition) <= 0:
        #         return
        #     self.check_conflicting_definitions(target, 'indexes')
        #     accumulator.add_definition('indexes', definition)
        # except Exception as e:
        #     raise SingleChoiceDefinitionFlowNodeException(self.name, [str(e)])


class _EnumStoreValuesNode(SingleChoiceDefinitionFlowNode):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self):
        super().__init__('enum-store-values-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        pass

    def get_dependencies(self) -> tuple[str]:
        return ('extract-values-node', )


class _EnumStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('enum-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = accumulator.get_definition('built')
        accumulator.add_definition('final', {} if definition is None else definition)

    def get_dependencies(self) -> tuple[str]:
        return ('enum-store-values-node', )


class _EnumDomainExtractCommentNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('enum-domain-extract-comment-node')


class _EnumDomainStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('enum-domain-store-final-definition-node')


enum_flow_builder\
    .at_work_path('validation')\
    .add_node(_EnumValidateSingleInheritedClassNode)\
    .at_work_path('extraction')\
    .add_node(_EnumExtractValuesNode).critical()\
    .at_work_path('store')\
        .add_node(_EnumDetermineIfTargetIsDomainNode).critical()\
        .build_choice(_EnumDomainExtractCommentNode)\
            .add_node(_EnumDomainStoreFinalDefinitionNode)\
            .end_choice()\
        .build_choice(_EnumStoreValuesNode)\
            .add_node(_EnumStoreFinalDefinitionNode)\
            .end_choice()

__all__ = {
    'pg_enum': pg_enum}

