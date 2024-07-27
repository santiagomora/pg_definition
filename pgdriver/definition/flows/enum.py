from pgdriver.definition.base import\
    FlowAccumulator,\
    TypeSubclassDefinitionFlow,\
    FlowComponent
from pgdriver.definition.tools import\
    pg_enum
from pgdriver.flows.common import\
    CommonValidateSingleInheritedClassComponent,\
    CommonExtractCommentDefinitionComponent


class EnumValidateSingleInheritedClassComponent(CommonValidateSingleInheritedClassComponent[pg_enum]):
    def get_dependencies(self) -> tuple[str]:
        return tuple()


# tengo que extraer los valores del enum para definirlo en postgres
class EnumExtractValuesComponent(FlowComponent[pg_enum]):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self):
        super().__init__('extract-values-component')

    def execute(self, target: type[pg_enum], accumulator: FlowAccumulator) -> None:
        pass

    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-target-metaclass-component',
                     'validate-single-inherited-class-component')


class EnumExtractCommentDefinitionComponent(CommonExtractCommentDefinitionComponent[pg_enum]):
    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-target-metaclass-component',
                     'validate-single-inherited-class-component')


class EnumStoreValuesComponent(FlowComponent[pg_enum]):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self):
        super().__init__('store-values-component')

    def execute(self, target: type[pg_enum], accumulator: FlowAccumulator) -> None:
        pass

    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-values-definition-component')


class EnumStoreCommentComponent(FlowComponent[pg_enum]):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self):
        super().__init__('store-comments-component')

    def execute(self, target: type[pg_enum], accumulator: FlowAccumulator) -> None:
        pass

    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-comment-component')


# para domains y enums cambia un poco porque entra por metaclase, con lo cual issubclass va a fallar
class EnumDefinitionFlow(TypeSubclassDefinitionFlow[pg_enum]):
    def __init__(self):
        super().__init__('pgdriver-enum-definition-flow')


pgenum_definition_flow: EnumDefinitionFlow = EnumDefinitionFlow()

with pgenum_definition_flow.at_path('validation') as flow:
    flow.register(EnumValidateSingleInheritedClassComponent())

    with pgenum_definition_flow.at_path('extraction') as flow:
        flow.register(EnumExtractValuesComponent().critical())
        flow.register(EnumExtractCommentDefinitionComponent())

with pgenum_definition_flow.at_path('final') as flow:
    flow.register(EnumStoreValuesComponent().critical())
    flow.register(EnumStoreCommentComponent())


__all__ = {'pgenum_definition_flow': pgenum_definition_flow}
