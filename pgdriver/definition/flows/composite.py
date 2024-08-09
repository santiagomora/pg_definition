from pgdriver.definition.flows import\
    FlowComponent,\
    FlowAccumulator,\
    TypeSubclassDefinitionFlow,\
    FlowComponentException
from typing import\
    Any,\
    Optional
from pgdriver.definition.flows.common import\
    CommonValidateSingleInheritedClassComponent,\
    CommonValidateRestrictedMetadataTypesComponent,\
    CommonValidateUniqueMetadataTypesComponent,\
    CommonValidateFieldsBaseTypeComponent,\
    CommonExtractCheckConstraintsComponent,\
    CommonStoreCheckConstraintsComponent
from pgdriver.definition.inspection import\
    extract_first_instance_from_field_metadata
from pgdriver.definition.build import\
    pg_attribute,\
    pg_domain,\
    pg_composite,\
    pg_enum,\
    pg_builtin,\
    pg_meta


class CompositeValidateSingleInheritedClassComponent(CommonValidateSingleInheritedClassComponent[pg_composite]):
    pass


class CompositeValidateRestrictedMetadataTypesComponent(CommonValidateRestrictedMetadataTypesComponent[pg_composite]):
    pass


class CompositeValidateUniqueMetadataTypesComponent(CommonValidateUniqueMetadataTypesComponent[pg_composite]):
    pass


class CompositeValidateFieldsBaseTypeComponent(CommonValidateFieldsBaseTypeComponent[pg_composite]):
    pass


class CompositeDependsOnValidationComponents:
    def get_dependencies(self) -> tuple[str]:
        return ('validate-single-inherited-class-component',
                'validate-restricted-metadata-types-component',
                'validate-unique-metadata-types-component',
                'validate-fields-base-type-component')


class CompositeExtractCheckDefinitionComponent(CommonExtractCheckConstraintsComponent[pg_composite],
                                               CompositeDependsOnValidationComponents):
    pass


class CompositeExtractAttributesDefinitionComponent(FlowComponent[pg_composite],
                                                    CompositeDependsOnValidationComponents):
    """
    Extract composite attributes
    """

    def __init__(self):
        super().__init__('extract-attributes-definition-component')

    def execute(self, target: type[pg_composite], accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de atributos
        attributes: list[dict[str, Any]] = []
        for name, info in target.model_fields.items():
            check: Optional[pg_meta.check] = extract_first_instance_from_field_metadata(info, pg_meta.check)
            attr_data: dict[str, Any] = {
                'attr_name': name,
                'attr_type': info.annotation}
            if check is not None:
                attr_data['attr_check'] = check
            attributes.append(attr_data)
        if len(attributes) > 0:
            accumulator.add_definition('columns', attributes)
        raise FlowComponentException(self.name, f'Class {target} must declare attributes.')


class CompositeStoreAttributesDefinitionComponent(FlowComponent[pg_composite]):
    def __init__(self):
        super().__init__('store-attributes-component')

    def execute(self, target: type[pg_composite], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('attributes', 'extraction')
        if definition is None:
            return
        attrs: list[pg_attribute] = [pg_attribute(**attr) for attr in definition]

        @classmethod
        def __pg_attributes(cls) -> list[pg_attribute]:
            return attrs

        accumulator.add_definition('__pg_attributes', __pg_attributes)

    def get_dependencies(self) -> tuple[str]:
        return ('extract-attributes-definition-component', )


class CompositeStoreCheckDefinitionComponent(CommonStoreCheckConstraintsComponent[pg_composite]):
    def get_dependencies(self) -> tuple[str]:
        return ('extract-check-constraints-component', )


class CompositeDefinitionFlow(TypeSubclassDefinitionFlow[pg_composite]):
    def __init__(self):
        super().__init__('pgdriver-composite-definition-flow')


pg_composite_definition_flow: CompositeDefinitionFlow = CompositeDefinitionFlow()

with pg_composite_definition_flow.at_work_path('validation') as flow:
    flow.register(CompositeValidateSingleInheritedClassComponent())
    flow.register(CompositeValidateRestrictedMetadataTypesComponent([
        pg_meta.check]))
    flow.register(CompositeValidateUniqueMetadataTypesComponent([
        pg_meta.check]))
    flow.register(CompositeValidateFieldsBaseTypeComponent(type_subclass=[
        pg_enum,
        pg_composite],
        type_instance=[
        pg_builtin,
        pg_domain]))

with pg_composite_definition_flow.at_work_path('extraction') as flow:
    flow.register(CompositeExtractCheckDefinitionComponent().critical())
    flow.register(CompositeExtractAttributesDefinitionComponent())

with pg_composite_definition_flow.at_work_path('final') as flow:
    flow.register(CompositeStoreAttributesDefinitionComponent().critical())
    flow.register(CompositeStoreCheckDefinitionComponent())


__all__ = {'pg_composite_definition_flow': pg_composite_definition_flow}
