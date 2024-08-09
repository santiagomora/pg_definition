from pgdriver.definition.flows import\
    FlowAccumulator,\
    TypeSubclassDefinitionFlow,\
    FlowComponent
from pgdriver.definition.build import\
    pg_enum
from pgdriver.definition.flows.common import\
    CommonValidateSingleInheritedClassComponent


class EnumValidateSingleInheritedClassComponent(CommonValidateSingleInheritedClassComponent[pg_enum]):
    def get_dependencies(self) -> tuple[str]:
        return tuple()


class EnumDependsOnValidationComponents:
    def get_dependencies(self) -> tuple[str]:
        return ('validate-single-inherited-class-component', )


class EnumExtractValuesComponent(FlowComponent[pg_enum],
                                 EnumDependsOnValidationComponents):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self):
        super().__init__('extract-values-component')

    def execute(self, target: type[pg_enum], accumulator: FlowAccumulator) -> None:
        pass


class EnumStoreValuesComponent(FlowComponent[pg_enum]):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self):
        super().__init__('store-values-component')

    def execute(self, target: type[pg_enum], accumulator: FlowAccumulator) -> None:
        pass

    def get_dependencies(self) -> tuple[str]:
        return ('extract-values-component', )


class EnumDefinitionFlow(TypeSubclassDefinitionFlow[pg_enum]):
    def __init__(self):
        super().__init__('pgdriver-enum-definition-flow')


pg_enum_definition_flow: EnumDefinitionFlow = EnumDefinitionFlow()

with pg_enum_definition_flow.at_work_path('validation') as flow:
    flow.register(EnumValidateSingleInheritedClassComponent())

    with pg_enum_definition_flow.at_work_path('extraction') as flow:
        flow.register(EnumExtractValuesComponent().critical())

with pg_enum_definition_flow.at_work_path('final') as flow:
    flow.register(EnumStoreValuesComponent().critical())


__all__ = {'pg_enum_definition_flow': pg_enum_definition_flow}
