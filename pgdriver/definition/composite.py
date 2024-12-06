from typing import\
    Any
from .common.flow import\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator,\
    FlowEndException,\
    FlowNodeException,\
    DefinitionFlowNode,\
    DefinitionFlowBuilder,\
    CommonDetermineIfTargetIsDomainNode
from .common.model import\
    composite_definition_flow_root,\
    composite,\
    table,\
    ModelValidateRestrictedMetadataTypesNode,\
    ModelValidateUniqueMetadataTypesNode,\
    ModelValidateFieldsBaseTypeNode,\
    ModelDiscardMetaInstancesFromInheritedFieldsNode,\
    ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode,\
    ModelExtractCheckConstraintsNode
from .builtin import\
    builtin
from .enums import\
    enums
from .meta import\
    check,\
    comment,\
    LogicOperand,\
    OperandDefinitionContext
from .common.inspection import\
    extract_definition_fields,\
    get_field_parent_definition,\
    extract_first_instance_from_field_metadata,\
    extract_by_instance_type_from_model_fields_info
from functools import\
    reduce


composite_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(composite_definition_flow_root)

"""
Some observations on postgres composite types

1. composite types cannot directly define check constraints, this is, user wont
be able to use check when defining a direct descendant of composite,
but this situation changes when defining a domain. Postgres allows user to declare
check constraints on domain types, so a composite domain has a totally different
workflow than a composite type.

2. comments on composite types or composite domains attributes are not supported.
"""


class _CompositeValidateFieldsBaseTypeNode(ModelValidateFieldsBaseTypeNode):
    def __init__(self):
        super().__init__('composite-validate-fields-base-type-node',
                         type_subclass=[enums, builtin, composite, table],
                         type_instance=[builtin])


class _CompositeValidateRestrictedMetadataTypesNode(ModelValidateRestrictedMetadataTypesNode):
    def __init__(self):
        super().__init__('composite-validate-restricted-metadata-types-node',
                         types=[comment])


class _CompositeValidateUniqueMetadataTypesNode(ModelValidateUniqueMetadataTypesNode):
    def __init__(self):
        super().__init__('composite-validate-unique-metadata-types-node',
                         types=[comment])


class _CompositeDependsOnValidationNodes:
    def get_dependencies(self) -> tuple[str]:
        return ('composite-validate-fields-base-type-node'
                'composite-validate-single-inherited-class-node',
                'composite-validate-unique-metadata-types-node',
                'composite-validate-restricted-metadata-types-node')


class _CompositeExtractAttributesDefinitionNode(SingleChoiceDefinitionFlowNode,
                                                _CompositeDependsOnValidationNodes):
    """
    Extract composite attributes
    """

    def __init__(self):
        super().__init__('composite-extract-attributes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de atributos
        attributes: dict[str, dict[str, Any]] = {}
        for name, info in extract_definition_fields(target):
            attributes[name] = {
                'name': name,
                'type': info.annotation,
                'comment': extract_first_instance_from_field_metadata(info, comment)}
        if len(attributes) <= 0:
            raise FlowNodeException(self.name, [f'Class {target} must declare attributes.'])
        accumulator.add_definition('attributes', attributes)


class _CompositeStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('composite-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, str] = dict()
        definition['type'] = target
        definition['attributes'] = accumulator.get_definition('attributes', 'extraction')
        definition['comment'] = None
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('composite-extract-attributes-node', )


class _CompositeDetermineIfTargetIsDomainNode(CommonDetermineIfTargetIsDomainNode,
                                              _CompositeDependsOnValidationNodes):
    def __init__(self):
        super().__init__('composite-determine-if-target-is-domain-node', composite)

    def get_next(self, accumulator: FlowAccumulator) -> DefinitionFlowNode:
        try:
            if self.is_domain:
                return self._nodes['composite-domain-validate-restricted-metadata-types-node']
            return self._nodes['composite-validate-restricted-metadata-types-node']
        except KeyError as e:
            raise FlowEndException(f'Choice not found in node {self.name}: {str(e)}')


class _CompositeDomainValidateRestrictedMetadataTypesNode(ModelValidateRestrictedMetadataTypesNode):
    def __init__(self):
        super().__init__('composite-domain-validate-restricted-metadata-types-node',
                         types=[check])


class _CompositeDomainValidateAttributesNode(SingleChoiceDefinitionFlowNode):
    """
    Validate composite attributes, there's two  scenarios according to the base class:
    1. direct inheritance from composite: it can declare any set of attributes
    2. inheritance from a composite subclass: declared type can only override 
    base class attributes. it cannot declare additional fields.
    """

    def __init__(self):
        super().__init__('composite-domain-validate-declared-attributes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        for name in target.model_fields:
            field_in_parent: Optional[FieldInfo] = get_field_parent_definition(name, target)
            if field_in_parent is None:
                raise FlowNodeException(self.name, [f'Additional attribute {name} detected in composite domain definition'])
            elif field_in_parent.annotation != target.model_fields[name].annotation:
                raise FlowNodeException(self.name, [f'Composite domain attribute type must match type in parent definition. Expected {target.model_fields[name].annotation} to be {field_in_parent.annotation}'])


class _CompositeDomainValidateSameTypeMetaInstancesHaveDifferentNamesNode(ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode):
    def __init__(self):
        super().__init__('composite-domain-validate-same-type-meta-instances-have-different-names-node',
                         types=[check])

class _CompositeDomainDependsOnValidationNodes:
    def get_dependencies(self) -> tuple[str]:
        return ('composite-validate-fields-base-type-node'
                'composite-validate-single-inherited-class-node',
                'composite-domain-validate-declared-attributes-node',
                'composite-domain-validate-same-type-meta-instances-have-different-names-node',
                'composite-domain-validate-unique-metadata-types-node',
                'composite-domain-validate-declared-attributes-node')


class _CompositeDomainExtractAttributesDefinitionNode(SingleChoiceDefinitionFlowNode, _CompositeDomainDependsOnValidationNodes):
    """
    Extract composite attributes
    """

    def __init__(self):
        super().__init__('composite-domain-extract-attributes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de atributos
        attributes: dict[str, dict[str, Any]] = {}
        for name, info in extract_definition_fields(target):
            attributes[name] = {
                'name': name,
                'type': info.annotation}
        accumulator.add_definition('attributes', attributes)


class _CompositeDomainExtractCheckConstraintNode(ModelExtractCheckConstraintsNode):
    def __init__(self):
        super().__init__('composite-domain-extract-check-constraints-node',
                         OperandDefinitionContext.COMPOSITE_DOMAIN)


class _CompositeDomainDiscardMetaInstancesFromInheritedFieldsNode(ModelDiscardMetaInstancesFromInheritedFieldsNode, _CompositeDependsOnValidationNodes):
    def __init__(self):
        super().__init__('composite-domain-discard-meta-instances-from-inherited-fields-node')


class _CompositeDomainStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('composite-domain-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = dict()
        definition['type'] = target
        definition['base_type'] = target.__bases__[0]
        definition['comment'] = None
        definition['attributes'] = accumulator.get_definition('attributes', 'extraction')
        definition['check'] = accumulator.get_definition('check_constraints', 'extraction')
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('composite-domain-extract-attributes-node',
				'composite-domain-discard-meta-instances-from-inherited-fields-node',
                'composite-domain-extract-check-constraints-node' )


composite_flow_builder\
    .at_work_path('validation')\
        .add_node(_CompositeValidateFieldsBaseTypeNode)\
        .add_node(_CompositeDetermineIfTargetIsDomainNode)\
    .build_choice(_CompositeValidateRestrictedMetadataTypesNode)\
        .add_node(_CompositeValidateUniqueMetadataTypesNode).critical()\
        .at_work_path('extraction')\
            .add_node(_CompositeExtractAttributesDefinitionNode)\
        .at_work_path('')\
            .add_node(_CompositeStoreFinalDefinitionNode).critical()\
        .end_choice()\
    .build_choice(_CompositeDomainValidateRestrictedMetadataTypesNode)\
        .at_work_path('validation')\
            .add_node(_CompositeDomainValidateAttributesNode).critical()\
            .add_node(_CompositeDomainValidateSameTypeMetaInstancesHaveDifferentNamesNode)\
        .at_work_path('extraction')\
            .add_node(_CompositeDomainExtractAttributesDefinitionNode).critical()\
            .add_node(_CompositeDomainExtractCheckConstraintNode)\
            .add_node(_CompositeDomainDiscardMetaInstancesFromInheritedFieldsNode)\
        .at_work_path('')\
            .add_node(_CompositeDomainStoreFinalDefinitionNode).critical()\
            .end_choice()

__all__ = {'composite': composite}
