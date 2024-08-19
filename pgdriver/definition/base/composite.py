from pgdriver.definition.build.common.flow import\
    FlowComponent,\
    FlowAccumulator,\
    DefinitionFlow,\
    FlowComponentException
from pgdriver.definition.build.common.component import\
    CommonValidateSingleInheritedClassComponent,\
    CommonValidateRestrictedMetadataTypesComponent,\
    CommonValidateUniqueMetadataTypesComponent,\
    CommonValidateFieldsBaseTypeComponent,\
    CommonExtractCheckConstraintsComponent,\
    CommonStoreCheckConstraintsComponent
from typing import\
    Any,\
    Optional
from pgdriver.definition.inspection import\
    extract_first_instance_from_field_metadata
from pgdriver.definition.build import\
    pg_domain,\
    pg_enum,\
    pg_builtin
from pgdriver.definition.extraction.base import\
    pg_attribute_definition
from pydantic import\
    BaseModel
from pgdriver.definition.build.common.meta import\
    check,\
    comment


class pg_composite_meta:
    class comment(comment):
        pass

    class check(check):
        pass


pg_composite_definition_flow: DefinitionFlow = DefinitionFlow('pgdriver-composite-definition-flow')


class pg_composite(BaseModel):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        accumulator: FlowAccumulator = FlowAccumulator()
        pg_composite_definition_flow.execute(cls, accumulator)


class CompositeValidateSingleInheritedClassComponent(CommonValidateSingleInheritedClassComponent):
    pass


class CompositeValidateRestrictedMetadataTypesComponent(CommonValidateRestrictedMetadataTypesComponent):
    pass


class CompositeValidateUniqueMetadataTypesComponent(CommonValidateUniqueMetadataTypesComponent):
    pass


class CompositeValidateFieldsBaseTypeComponent(CommonValidateFieldsBaseTypeComponent):
    pass


class CompositeDependsOnValidationComponents:
    def get_dependencies(self) -> tuple[str]:
        return ('validate-single-inherited-class-component',
                'validate-restricted-metadata-types-component',
                'validate-unique-metadata-types-component',
                'validate-fields-base-type-component')


class CompositeExtractCheckDefinitionComponent(CommonExtractCheckConstraintsComponent,
                                               CompositeDependsOnValidationComponents):
    pass


class CompositeExtractAttributesDefinitionComponent(FlowComponent,
                                                    CompositeDependsOnValidationComponents):
    """
    Extract composite attributes
    """

    def __init__(self):
        super().__init__('extract-attributes-definition-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de atributos
        attributes: list[dict[str, Any]] = []
        for name, info in target.model_fields.items():
            check: Optional[pg_composite_meta.check] = extract_first_instance_from_field_metadata(info, pg_composite_meta.check)
            attr_data: dict[str, Any] = {
                'name': name,
                'type_name': info.annotation}
            if check is not None:
                attr_data['check_constraint'] = check
            comment: Optional[pg_composite_meta.comment] = extract_first_instance_from_field_metadata(info, pg_composite_meta.comment)
            attr_data['comment'] = comment
            attributes.append(attr_data)
        if len(attributes) <= 0:
            raise FlowComponentException(self.name, f'Class {target} must declare attributes.')
        accumulator.add_definition('attributes', attributes)


class CompositeStoreAttributesDefinitionComponent(FlowComponent):
    def __init__(self):
        super().__init__('store-attributes-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('attributes', 'extraction')

        attrs: list[pg_attribute_definition] = [] if definition is None else [
            pg_attribute_definition(**attr) for attr in definition]

        @classmethod
        def __pg_attributes(cls) -> list[pg_attribute_definition]:
            return attrs

        accumulator.add_definition('__pg_attributes', __pg_attributes)

    def get_dependencies(self) -> tuple[str]:
        return ('extract-attributes-definition-component', )


class CompositeStoreCheckDefinitionComponent(CommonStoreCheckConstraintsComponent):
    def get_dependencies(self) -> tuple[str]:
        return ('extract-check-constraints-component', )


class CompositeStoreFinalDefinitionComponent(FlowComponent):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('store-final-definition-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = accumulator.get_definition('built')
        accumulator.add_definition('final', {} if definition is None else definition)

    def get_dependencies(self) -> tuple[str]:
        return ('store-check-constraints-component', )


with pg_composite_definition_flow.at_work_path('validation') as flow:
    flow.register(CompositeValidateSingleInheritedClassComponent())
    flow.register(CompositeValidateRestrictedMetadataTypesComponent([
        pg_composite_meta.check]))
    flow.register(CompositeValidateUniqueMetadataTypesComponent([
        pg_composite_meta.check]))
    flow.register(CompositeValidateFieldsBaseTypeComponent(
        type_subclass=[
            pg_enum,
            pg_composite],
        type_instance=[
            pg_builtin,
            pg_domain]))

with pg_composite_definition_flow.at_work_path('extraction') as flow:
    flow.register(CompositeExtractCheckDefinitionComponent().critical())
    flow.register(CompositeExtractAttributesDefinitionComponent())

with pg_composite_definition_flow.at_work_path('built') as flow:
    flow.register(CompositeStoreAttributesDefinitionComponent().critical())
    flow.register(CompositeStoreCheckDefinitionComponent())

with pg_composite_definition_flow.at_work_path('') as flow:
    flow.register(CompositeStoreFinalDefinitionComponent().critical())


__all__ = {'pg_composite_definition_flow': pg_composite_definition_flow}
