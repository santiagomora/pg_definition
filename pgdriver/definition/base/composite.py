from pydantic import\
    BaseModel
from typing import\
    Any,\
    Optional
from .common.flow import\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    DefinitionFlowNodeFactory,\
    FlowEndException,\
    FlowNodeException,\
    DefinitionFlowNode
from .common.node import\
    CommonValidateRestrictedMetadataTypesNode,\
    CommonValidateUniqueMetadataTypesNode,\
    CommonValidateFieldsBaseTypeNode,\
    CommonExtractCheckConstraintsNode,\
    CommonStoreCheckConstraintsNode,\
    CommonMergeInheritedFieldsNode,\
    CommonDetermineIfTargetIsDomainNode,\
    CommonValidateSingleInheritedClassNode
from .domain import\
    DomainExtractCommentNode,\
    DomainStoreFinalDefinitionNode
from .builtin import\
    pg_builtin
from .enums import\
    pg_enum
from ..extraction.base import\
    pg_attribute_definition
from .common.meta import\
    pg_model_field_check,\
    pg_comment
from ..inspection import\
    extract_by_instance_type_from_inherited_classes,\
    extract_definition_fields,\
    is_field_inherited,\
    extract_first_instance_from_field_metadata


class pg_composite_meta:
    class comment(pg_comment):
        pass

    class check(pg_model_field_check):
        pass


_pg_composite_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('composite-definition-flow')


class pg_composite(BaseModel, frozen=True):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        accumulator: FlowAccumulator = FlowAccumulator(cls)
        _pg_composite_definition_flow_root.execute(cls, accumulator)


class _CompositeValidateSingleInheritedClassNode(CommonValidateSingleInheritedClassNode):
    def __init__(self):
        super().__init__('composite-validate-single-inherited-class-node')


class _CompositeValidateRestrictedMetadataTypesNode(CommonValidateRestrictedMetadataTypesNode):
    def __init__(self,
                 restricted: list[type]):
        super().__init__('composite-validate-declared-attributes-node',
                         restricted)


class _CompositeValidateUniqueMetadataTypesNode(CommonValidateUniqueMetadataTypesNode):
    def __init__(self,
                 unique: list[type]):
        super().__init__('composite-validate-unique-metadata-types-node',
                         unique)


class _CompositeValidateFieldsBaseTypeNode(CommonValidateFieldsBaseTypeNode):
    def __init__(self,
                 *,
                 type_subclass: list[type],
                 type_instance: list[type]):
        super().__init__('composite-validate-fields-base-type-node',
                         type_subclass=type_subclass,
                         type_instance=type_instance)


class _CompositeValidateAttributesNode(SingleChoiceDefinitionFlowNode):
    """
    Validate composite attributes, there's two  scenarios according to the base class:
    1. direct inheritance from pg_composite: it can declare any set of attributes
    2. inheritance from a pg_composite subclass: declared type can only override 
    base class attributes. it cannot declare additional fields
    """

    def __init__(self):
        super().__init__('composite-validate-declared-attributes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        base_classes: tuple[type] = extract_by_instance_type_from_inherited_classes(target)
        base_class: type = base_classes[0]
        if base_class is pg_composite:
            return
        for name, info in extract_definition_fields(target):
            if not is_field_inherited(name,
                                      target,
                                      pg_composite):
                raise FlowNodeException(f'Additional attribute {name} detected in composite domain definition')


class _CompositeDependsOnValidationNodes:
    def get_dependencies(self) -> tuple[str]:
        return ('composite-validate-single-inherited-class-node',
                'composite-validate-restricted-metadata-types-node',
                'composite-validate-unique-metadata-types-node',
                'composite-validate-fields-base-type-node',
                'composite-validate-declared-attributes-node')


class _CompositeMergeInheritedFieldsNode(CommonMergeInheritedFieldsNode,
                                         _CompositeDependsOnValidationNodes):
    def __init__(self):
        super().__init__('composite-common-merge-inherited-fields-node',
                         pg_composite,
                         (pg_composite_meta.check),
                         (pg_composite_meta.check))


class _CompositeDependsOnValidationAndMergeNodes(_CompositeDependsOnValidationNodes):
    def get_dependencies(self) -> tuple[str]:
        return (*(super().get_dependencies()),
                'composite-merge-inherited-fields-node')


class _CompositeExtractCheckDefinitionNode(CommonExtractCheckConstraintsNode,
                                           _CompositeDependsOnValidationAndMergeNodes):
    def __init__(self):
        super().__init__('composite-extract-check-constraints-node')


class _CompositeExtractAttributesDefinitionNode(SingleChoiceDefinitionFlowNode,
                                                _CompositeDependsOnValidationAndMergeNodes):
    """
    Extract composite attributes
    """

    def __init__(self):
        super().__init__('composite-extract-attributes-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de atributos
        attributes: list[dict[str, Any]] = []
        for name, info in target.model_fields.items():
            check: Optional[pg_composite_meta.check] = extract_first_instance_from_field_metadata(info,
                                                                                                  pg_composite_meta.check)
            attr_data: dict[str, Any] = {
                'name': name,
                'type_name': info.annotation}
            if check is not None:
                attr_data['check_constraint'] = check.as_str()
            comment: Optional[pg_composite_meta.comment] = extract_first_instance_from_field_metadata(info,
                                                                                                      pg_composite_meta.comment)
            attr_data['comment'] = comment
            attributes.append(attr_data)
        if len(attributes) <= 0:
            raise FlowNodeException(self.name, f'Class {target} must declare attributes.')
        accumulator.add_definition('attributes',
                                   attributes)


class _CompositeDetermineIfTargetIsDomainNode(CommonDetermineIfTargetIsDomainNode):
    def __init__(self):
        super().__init__('composite-common-determine-if-target-is-domain-node',
                         pg_composite)

    def get_next(self,
                 accumulator: FlowAccumulator) -> DefinitionFlowNode:
        try:
            if self.is_domain:
                return self._nodes['composite-store-check-constraint-node']
            return self._nodes['composite-store-attributes-node']
        except KeyError as e:
            raise FlowEndException(f'Choice not found in node {self.name}: {str(e)}')


class _CompositeStoreAttributesDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('composite-store-attributes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('attributes',
                                                                      'extraction')
        attrs: list[pg_attribute_definition] = [] if definition is None else [
            pg_attribute_definition(**attr) for attr in definition]

        @classmethod
        def __pg_attributes(cls) -> list[pg_attribute_definition]:
            return attrs

        accumulator.add_definition('__pg_attributes',
                                   __pg_attributes)

    def get_dependencies(self) -> tuple[str]:
        return ('composite-extract-attributes-node', )


class _CompositeStoreCheckDefinitionNode(CommonStoreCheckConstraintsNode):
    def __init__(self) -> None:
        super().__init__('composite-store-check-constraints-node')

    def get_dependencies(self) -> tuple[str]:
        return ('composite-extract-check-constraints-node', )


class _CompositeStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('composite-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = accumulator.get_definition('built')
        accumulator.add_definition('final', {} if definition is None else definition)

    def get_dependencies(self) -> tuple[str]:
        return ('composite-store-check-constraints-node', )


class _CompositeDomainExtractCommentNode(DomainExtractCommentNode):
    def __init__(self):
        super().__init__('composite-domain-extract-comment-node')


class _CompositeDomainStoreFinalDefinitionNode(DomainStoreFinalDefinitionNode):
    def __init__(self):
        super().__init__('composite-domain-store-final-definition-node')


_composite_node_factory: DefinitionFlowNodeFactory = DefinitionFlowNodeFactory()

# we build domain definition flow
_domain_flow_first_node: Optional[DefinitionFlowNode] = None
_domain_flow_last_node: Optional[DefinitionFlowNode] = None

with _composite_node_factory.at_work_path('extraction') as fact:
    _domain_flow_first_node = _domain_flow_last_node =\
        fact.get_definition_node(_CompositeDomainExtractCommentNode)

with _composite_node_factory.at_work_path('final') as fact:
    _domain_flow_last_node = _domain_flow_last_node\
        .set_next(fact.get_definition_node(_CompositeDomainStoreFinalDefinitionNode))


# we build composite definition flow
_composite_flow_store_first_node: Optional[DefinitionFlowNode] = None
_composite_flow_store_last_node: Optional[DefinitionFlowNode] = None

with _composite_node_factory.at_work_path('store') as fact:
    _composite_flow_store_first_node = _composite_flow_store_last_node =\
        fact.get_definition_node(_CompositeStoreAttributesDefinitionNode).critical()
    _composite_flow_store_last_node = _composite_flow_store_last_node\
        .set_next(fact.get_definition_node(_CompositeStoreCheckDefinitionNode))

with _composite_node_factory.at_work_path('final') as fact:
    _composite_flow_store_last_node = _composite_flow_store_last_node\
        .set_next(fact.get_definition_node(_CompositeStoreFinalDefinitionNode).critical())


# we build the final definition flow, that joins both domain and composite flows
_composite_flow_last_node: Optional[DefinitionFlowNode] = None

with _composite_node_factory.at_work_path('validation') as fact:
    _composite_flow_last_node = _pg_composite_definition_flow_root\
        .set_next(fact.get_definition_node(_CompositeValidateSingleInheritedClassNode))
    _composite_flow_last_node = _composite_flow_last_node\
        .set_next(fact.get_definition_node(_CompositeValidateRestrictedMetadataTypesNode,
                                           [pg_composite_meta.check]))\
        .set_next(fact.get_definition_node(_CompositeValidateUniqueMetadataTypesNode,
                                           [pg_composite_meta.check,
                                            pg_composite_meta.comment]))\
        .set_next(fact.get_definition_node(_CompositeValidateFieldsBaseTypeNode,
                                           type_subclass=[pg_enum,
                                                          pg_builtin,
                                                          pg_composite],
                                           type_instance=[pg_builtin]))

with _composite_node_factory.at_work_path('merge') as fact:
    _composite_flow_last_node = _composite_flow_last_node.\
        set_next(fact.get_definition_node(_CompositeMergeInheritedFieldsNode).critical())

with _composite_node_factory.at_work_path('extraction') as fact:
    _composite_flow_last_node = _composite_flow_last_node\
        .set_next(fact.get_definition_node(_CompositeExtractCheckDefinitionNode).critical())\
        .set_next(fact.get_definition_node(_CompositeExtractAttributesDefinitionNode))

with _composite_node_factory.at_work_path('store') as fact:
    _composite_flow_last_node = _composite_flow_last_node\
        .set_next(fact.get_definition_node(_CompositeDetermineIfTargetIsDomainNode).critical())\
        .set_next(_composite_flow_store_first_node)\
        .set_next(_domain_flow_first_node)

__all__ = {
    'pg_composite': pg_composite,
    'pg_composite_meta': pg_composite_meta}
