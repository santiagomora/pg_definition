from pgdriver.definition.base import\
    FlowComponent,\
    FlowAccumulator
from pgdriver.definition.tools import\
    pg_composite


class CompositeExtractAttributesDefinitionComponent(FlowComponent[pg_composite]):
    """
    Extract composite attributes
    """

    def __init__(self):
        super().__init__('extract-attributes-definition-component')

    def execute(self, target: type[pg_composite], accumulator: FlowAccumulator) -> None:
        pass


class CompositeExtractCheckDefinitionComponent(FlowComponent[pg_composite]):
    """
    Extract check constraints from metadata
    """

    def __init__(self):
        super().__init__('extract-check-definition-component')

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        attr_name: str = f'_{target.__name__}__pg_check_meta'
        if hasattr(target, attr_name):
            check: pg_check_meta = getattr(target, attr_name)()
            accumulator.add_definition('check', check.predicate.as_str(target.__name__))
