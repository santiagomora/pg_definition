from pgdriver.definition.base import\
    FlowAccumulator,\
    FlowComponent
from pgdriver.definition.tools import\
    pg_enum


class EnumValidateTargetMetaclassComponent(FlowComponent[pg_enum]):
    """
    Enum must be a subclass of pg_enum
    """

    def __init__(self, restricted: list[type]):
        super().__init__('enum-validate-target-class-component')
        self._restricted = restricted

    def execute(self, target: type[pg_enum], accumulator: FlowAccumulator) -> None:
        pass


# tengo que extraer los valores del enum para definirlo en postgres
class EnumExtractValuesComponent(FlowComponent[pg_enum]):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self, restricted: list[type]):
        super().__init__('enum-extract-values-component')
        self._restricted = restricted

    def execute(self, target: type[pg_enum], accumulator: FlowAccumulator) -> None:
        pass
