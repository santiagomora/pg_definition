from pgdriver.adapt.pydantic import\
    PGBaseModel
from abc import\
    ABC
from pgdriver.definition.flow import\
    DefinitionFlow,\
    FlowComponent,\
    FlowComponentException,\
    FlowAccumulator
from pgdriver.definition.types.metadata import\
    pg_comment,\
    pg_check


class pg_composite(PGBaseModel, ABC):
    pass


pgcomposite_definition_flow: DefinitionFlow[pg_composite] = DefinitionFlow[pg_composite]('pgdriver-composite-definition-flow', pg_composite)


class ValidateTargetMetaclassComponent(FlowComponent[pg_composite]):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self, restricted: list[type]):
        super().__init__('validate-target-metaclass-component')
        self._restricted = restricted

    def execute(self, target: type[pg_composite], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        if not isinstance(target, pg_composite):
            errors.append(f'Target type {type.__name__} must be a pg_composite instance')
        if not isinstance(target, pg_builtin):
            errors.append(f'Target type {type.__name__} must be a pg_builtin instance')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


pgcomposite_definition_flow.register_component(
    ValidateTargetMetaclassComponent())


class ExtractCommentDefinitionComponent(FlowComponent[pg_composite]):
    """
    Extract domain comments
    """

    def __init__(self):
        super().__init__('extract-comment-definition-component')

    def execute(self, target: type[pg_composite], accumulator: FlowAccumulator) -> None:
        attr_name: str = f'_{target.__name__}__pg_comment'
        if hasattr(target, attr_name):
            comment: pg_comment = getattr(target, attr_name)()
            accumulator.add_definition('comment', comment.value)


class ExtractCheckDefinitionComponent(FlowComponent[pg_composite]):
    """
    Extract domain check constraints
    """

    def __init__(self):
        super().__init__('extract-check-definition-component')

    def execute(self, target: type[pg_composite], accumulator: FlowAccumulator) -> None:
        attr_name: str = f'_{target.__name__}__pg_check'
        if hasattr(target, attr_name):
            check: pg_check = getattr(target, attr_name)()
            accumulator.add_definition('check', check.predicate.as_str(target.__name__))


class ExtractAttributesDefinitionComponent(FlowComponent[pg_composite]):
    """
    Extract domain check constraints
    """

    def __init__(self):
        super().__init__('extract-attributes-definition-component')

    def execute(self, target: type[pg_composite], accumulator: FlowAccumulator) -> None:
        pass


pgcomposite_definition_flow.register_component(
    ExtractCommentDefinitionComponent())

pgcomposite_definition_flow.register_component(
    ExtractCheckDefinitionComponent())

pgcomposite_definition_flow.register_component(
    ExtractAttributesDefinitionComponent())

pgcomposite_definition_flow.set_critical_component('extract-comment-definition-component')
