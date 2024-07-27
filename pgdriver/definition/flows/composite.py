from pgdriver.definition.flows import\
    FlowComponent,\
    FlowAccumulator,\
    TypeSubclassDefinitionFlow,\
    FlowComponentException
from typing import\
    Any,\
    Optional
from pgdriver.flows.common import\
    CommonValidateSingleInheritedClassComponent,\
    CommonValidateRestrictedMetadataTypesComponent,\
    CommonValidateUniqueMetadataTypesComponent,\
    CommonValidateFieldsBaseTypeComponent,\
    CommonExtractCommentDefinitionComponent,\
    CommonExtractCheckConstraintsComponent,\
    CommonStoreCheckConstraintsComponent
from pgdriver.definition.inspection import\
    extract_first_instance_from_field_metadata
from pgdriver.definition.metadata import\
    pg_check_meta
from pgdriver.definition.build import\
    pg_attribute,\
    pg_domain,\
    pg_composite,\
    pg_enum,\
    pg_builtin


class CompositeValidateSingleInheritedClassComponent(CommonValidateSingleInheritedClassComponent[pg_composite]):
    def get_dependencies(self) -> tuple[str]:
        return tuple()


class CompositeValidateRestrictedMetadataTypesComponent(CommonValidateRestrictedMetadataTypesComponent[pg_composite]):
    def get_dependencies(self) -> tuple[str]:
        return tuple()


class CompositeValidateUniqueMetadataTypesComponent(CommonValidateUniqueMetadataTypesComponent[pg_composite]):
    def get_dependencies(self) -> tuple[str]:
        return tuple()


class CompositeValidateFieldsBaseTypeComponent(CommonValidateFieldsBaseTypeComponent[pg_composite]):
    def get_dependencies(self) -> tuple[str]:
        return tuple()


class CompositeExtractCommentDefinitionComponent(CommonExtractCommentDefinitionComponent[pg_composite]):
    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-single-inherited-class-component',
                     'validate-restricted-metadata-types-component',
                     'validate-unique-metadata-types-component',
                     'validate-fields-base-type-component')


class CompositeExtractCheckDefinitionComponent(CommonExtractCheckConstraintsComponent[pg_composite]):
    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-single-inherited-class-component',
                     'validate-restricted-metadata-types-component',
                     'validate-unique-metadata-types-component',
                     'validate-fields-base-type-component')


class CompositeExtractAttributesDefinitionComponent(FlowComponent[pg_composite]):
    """
    Extract composite attributes
    """

    def __init__(self):
        super().__init__('extract-attributes-definition-component')

    def execute(self, target: type[pg_composite], accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de atributos
        attributes: list[dict[str, Any]] = []
        for name, info in target.model_fields.items():
            check: Optional[pg_check_meta] = extract_first_instance_from_field_metadata(info, pg_check_meta)
            attr_data: dict[str, Any] = {
                'attr_name': name,
                'attr_type': info.annotation}
            if check is not None:
                attr_data['attr_check'] = check
            attributes.append(attr_data)
        if len(attributes) > 0:
            accumulator.add_definition('columns', attributes)
        raise FlowComponentException(self.name, f'Class {target.__name__} must declare attributes.')

    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-single-inherited-class-component',
                     'validate-restricted-metadata-types-component',
                     'validate-unique-metadata-types-component',
                     'validate-fields-base-type-component')


class CompositeStoreAttributesDefinitionComponent(FlowComponent[pg_composite]):
    def __init__(self):
        super().__init__('store-attributes-component')

    def execute(self, target: type[pg_composite], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('attributes', 'extraction')
        if definition is None:
            return
        attrs: list[pg_attribute] = [pg_attribute(**attr) for attr in definition]

        @classmethod
        def __pg_get_attributes(cls) -> list[pg_attribute]:
            return attrs

        accumulator.add_definition('__pg_get_attributes', __pg_get_attributes)

    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-attributes-definition-component')


class CompositeStoreCheckDefinitionComponent(CommonStoreCheckConstraintsComponent[pg_composite]):
    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-check-definition-component')


class CompositeDefinitionFlow(TypeSubclassDefinitionFlow[pg_composite]):
    def __init__(self):
        super().__init__('pgdriver-composite-definition-flow')


pgcomposite_definition_flow: CompositeDefinitionFlow = CompositeDefinitionFlow()

with pgcomposite_definition_flow.at_path('validation') as flow:
    flow.register(CompositeValidateSingleInheritedClassComponent())
    flow.register(CompositeValidateRestrictedMetadataTypesComponent([
        pg_check_meta]))
    flow.register(CompositeValidateUniqueMetadataTypesComponent([
        pg_check_meta]))
    flow.register(CompositeValidateFieldsBaseTypeComponent([
        pg_composite,
        pg_enum], [
        pg_builtin,
        pg_domain]))
    flow.register(CompositeValidateSingleInheritedClassComponent())
    flow.register(CompositeValidateRestrictedMetadataTypesComponent([
        pg_check_meta]))
    flow.register(CompositeValidateUniqueMetadataTypesComponent([
        pg_check_meta]))
    flow.register(CompositeValidateFieldsBaseTypeComponent([
        pg_composite,
        pg_enum], [
        pg_builtin,
        pg_domain]))

with pgcomposite_definition_flow.at_path('extraction') as flow:
    flow.register(CompositeExtractCommentDefinitionComponent().critical())
    flow.register(CompositeExtractCheckDefinitionComponent())
    flow.register(CompositeExtractAttributesDefinitionComponent())

with pgcomposite_definition_flow.at_path('final') as flow:
    flow.register(CompositeStoreAttributesDefinitionComponent().critical())
    flow.register(CompositeStoreCheckDefinitionComponent())


__all__ = {'pgcomposite_definition_flow': pgcomposite_definition_flow}
