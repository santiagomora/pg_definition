from pgdriver.definition.flows import\
    FlowAccumulator,\
    DefinitionFlow,\
    FlowComponent
from pgdriver.definition.extraction.base import\
    pg_enum_definition,\
    pg_enum_value_definition
from pgdriver.definition.flows.common import\
    CommonValidateSingleInheritedClassComponent
from typing import\
    Any
from enum import\
    Enum


pg_enum_definition_flow: DefinitionFlow = DefinitionFlow('pgdriver-enum-definition-flow')


class pg_enum(metaclass=Enum):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        accumulator: FlowAccumulator = FlowAccumulator()
        pg_enum_definition_flow.execute(cls, accumulator)


class EnumValidateSingleInheritedClassComponent(CommonValidateSingleInheritedClassComponent):
    def get_dependencies(self) -> tuple[str]:
        return tuple()


class EnumDependsOnValidationComponents:
    def get_dependencies(self) -> tuple[str]:
        return ('validate-single-inherited-class-component', )


class EnumExtractValuesComponent(FlowComponent,
                                 EnumDependsOnValidationComponents):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self):
        super().__init__('extract-values-component')

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
        #     raise FlowComponentException(self.name, [str(e)])


class EnumStoreValuesComponent(FlowComponent):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self):
        super().__init__('store-values-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        pass

    def get_dependencies(self) -> tuple[str]:
        return ('extract-values-component', )


class EnumStoreFinalDefinitionComponent(FlowComponent):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('store-final-definition-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = accumulator.get_definition('built')
        accumulator.add_definition('final', {} if definition is None else definition)

    def get_dependencies(self) -> tuple[str]:
        return ('store-values-component', )


with pg_enum_definition_flow.at_work_path('validation') as flow:
    flow.register(EnumValidateSingleInheritedClassComponent())

    with pg_enum_definition_flow.at_work_path('extraction') as flow:
        flow.register(EnumExtractValuesComponent().critical())

with pg_enum_definition_flow.at_work_path('built') as flow:
    flow.register(EnumStoreValuesComponent().critical())

with pg_enum_definition_flow.at_work_path('') as flow:
    flow.register(EnumStoreFinalDefinitionComponent().critical())


__all__ = {'pg_enum_definition_flow': pg_enum_definition_flow}
