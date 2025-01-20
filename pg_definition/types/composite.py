from typing import\
    Any,\
    Optional
from ..common.flow import\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator,\
    FlowException,\
    NodeException,\
    DefinitionFlowNode,\
    DefinitionFlowBuilder,\
    RootDefinitionFlowNode,\
    execute_definition_flow
from ..common.node import\
    CommonDetermineIfTargetIsDomainNode,\
    CommonValidateRestrictedMetadataTypesNode,\
    CommonValidateFieldsBaseTypeNode,\
    ModelValidateUniqueMetadataTypesNode,\
    ModelDiscardMetaInstancesFromInheritedFieldsNode,\
    ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode
from .builtin import\
    builtin,\
    compound
import base_types as bt
from .enums import\
    enum
from pg_definition.objects.comment import\
    comment
from pg_definition.objects.check import\
    check
from ..common.inspection import\
    extract_definition_fields,\
    get_field_parent_definition,\
    extract_first_instance_from_field_metadata,\
    extract_by_instance_type_from_model_fields_info
from pydantic.fields import\
    FieldInfo


__all__ = ['composite']


composite_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('composite-definition-flow')
composite_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(composite_definition_flow_root)


class CompositeOperandDefinitionContext(bt.OperandDefinitionContext):
    @classmethod
    def parse_field(cls, field_instance: bt.field) -> str:
        return f'(VALUE).{field_instance._fieldname}'

    @classmethod
    def parse_this(cls, this_instance: bt.this) -> str:
        print('culo')
        if this_instance._fieldname is None:
            raise ValueError(f'Operand {repr(this_instance)} definition not correctly propagated.')
        return f'(VALUE).{this_instance._fieldname}'


class composite(compound):
    def __new__(
        cls, clsname, clsbases, namespace
    ) -> type:
        rettype: type = super().__new__(
            cls, clsname, clsbases, namespace,
            inheritance_policy=bt.InheritancePolicy.FORCE_REDECLARATION
        )
        execute_definition_flow(rettype, composite_definition_flow_root)
        return rettype

    def definition_context(self) -> type[bt.OperandDefinitionContext]:
        return CompositeOperandDefinitionContext


class _CompositeValidateFieldsBaseTypeNode(CommonValidateFieldsBaseTypeNode):
    def __init__(self):
        super().__init__('composite-validate-fields-base-type-node',
                         type_subclass=[],
                         type_instance=[enum, builtin, compound])


class _CompositeValidateRestrictedMetadataTypesNode(CommonValidateRestrictedMetadataTypesNode):
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
            raise NodeException(self.name, [f'Class {target} must declare attributes.'])
        accumulator.add_definition('attributes', attributes)


class _CompositeStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('composite-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, str] = dict()
        definition['type'] = target
        definition['attributes'] = accumulator.get_definition('attributes', 'extraction')
        definition['comment'] = None
        definition['schema'] = None
        definition['kind'] = 'composite'
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('composite-extract-attributes-node', )


class _CompositeDetermineIfTargetIsDomainNode(CommonDetermineIfTargetIsDomainNode,
                                              _CompositeDependsOnValidationNodes):
    def __init__(self):
        super().__init__('composite-determine-if-target-is-domain-node')

    def get_next(self, accumulator: FlowAccumulator) -> DefinitionFlowNode:
        try:
            if self.is_domain:
                return self._nodes['composite-domain-validate-restricted-metadata-types-node']
            return self._nodes['composite-validate-restricted-metadata-types-node']
        except KeyError as e:
            raise FlowException(f'Choice not found in node {self.name}: {str(e)}')


class _CompositeDomainValidateRestrictedMetadataTypesNode(CommonValidateRestrictedMetadataTypesNode):
    def __init__(self):
        super().__init__('composite-domain-validate-restricted-metadata-types-node',
                         types=[check])

# 
# class _CompositeDomainValidateAttributesNode(SingleChoiceDefinitionFlowNode):
#     """
#     Validate composite attributes, there's two  scenarios according to the base class:
#     1. direct inheritance from composite: it can declare any set of attributes
#     2. inheritance from a composite subclass: declared type can only override 
#     base class attributes. it cannot declare additional fields.
#     """
# 
#     def __init__(self):
#         super().__init__('composite-domain-validate-declared-attributes-node')
# 
#     def execute(self, target: type, accumulator: FlowAccumulator) -> None:
#         for name in target.model_fields:
#             field_in_parent: Optional[FieldInfo] = get_field_parent_definition(name, target)
#             if field_in_parent is None:
#                 raise NodeException(self.name, [f'Additional attribute {name} detected in composite domain definition'])
#             elif field_in_parent.annotation != target.model_fields[name].annotation:
#                 raise NodeException(self.name, [f'Composite domain attribute type must match type in parent definition. Expected {target.model_fields[name].annotation} to be {field_in_parent.annotation}'])


class _CompositeDomainValidateSameTypeMetaInstancesHaveDifferentNamesNode(ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode):
    def __init__(self):
        super().__init__('composite-domain-validate-same-type-meta-instances-have-different-names-node',
                         types=[check])

class _CompositeDomainDependsOnValidationNodes:
    def get_dependencies(self) -> tuple[str]:
        return ('composite-validate-fields-base-type-node'
                'composite-validate-single-inherited-class-node',
                'composite-domain-validate-same-type-meta-instances-have-different-names-node',
                'composite-domain-validate-unique-metadata-types-node')


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


class _CompositeDomainExtractCheckConstraintNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('composite-domain-extract-check-constraints-node')
        self._context = CompositeOperandDefinitionContext

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        checks: dict[str, check] = {}
        for field, ck in extract_by_instance_type_from_model_fields_info(target, check):
            ck.predicate.propagate_definition(target.model_fields[field].annotation, field, self._context)
            ck.name = f'{target.__name__}_{ck.name}'
            checks[ck.name] = ck
        accumulator.add_definition('check_constraints', checks if checks != {} else None)


# class _CompositeDomainDiscardMetaInstancesFromInheritedFieldsNode(ModelDiscardMetaInstancesFromInheritedFieldsNode, _CompositeDependsOnValidationNodes):
#     def __init__(self):
#         super().__init__('composite-domain-discard-meta-instances-from-inherited-fields-node')


class _CompositeDomainStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('composite-domain-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = dict()
        definition['schema'] = None
        definition['type'] = target
        definition['base_type'] = target.__bases__[0]
        definition['comment'] = None
        definition['kind'] = 'domain'
        definition['attributes'] = accumulator.get_definition('attributes', 'extraction')
        definition['check'] = accumulator.get_definition('check_constraints', 'extraction')
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('composite-domain-extract-attributes-node',
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
            .add_node(_CompositeDomainValidateSameTypeMetaInstancesHaveDifferentNamesNode).critical()\
        .at_work_path('extraction')\
            .add_node(_CompositeDomainExtractAttributesDefinitionNode).critical()\
            .add_node(_CompositeDomainExtractCheckConstraintNode)\
        .at_work_path('')\
            .add_node(_CompositeDomainStoreFinalDefinitionNode).critical()\
            .end_choice()
# .add_node(_CompositeDomainDiscardMetaInstancesFromInheritedFieldsNode)\
