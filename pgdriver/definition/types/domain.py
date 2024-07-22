from pgdriver.definition.types.builtin import\
    pg_builtin
from pgdriver.definition.flow import\
    DefinitionFlow,\
    FlowAccumulator,\
    FlowComponentException,\
    FlowComponent
from pgdriver.definition.inspection import\
    extract_by_instance_type_from_inherited_classes
from pgdriver.definition.types.metadata import\
    pg_check,\
    pg_comment


# designed to be used as a metaclass
class pg_domain(pg_builtin):
    pass


def is_domain(cls: type):
    bases: tuple[type] = extract_by_instance_type_from_inherited_classes(cls)
    return pg_domain(cls.__name__, bases, dict(cls.__dict__))


# the pg_domain is meant to be used as a metaclass, so all the classes will be
# instances of pg_domain, not subclasses, this typing annotations are wrongly
# designed as flows that use pg_table differ from pg_domain
pgdomain_definition_flow: DefinitionFlow[pg_domain] = DefinitionFlow[pg_domain]('pgdriver-domain-definition-flow', pg_domain)


class ValidateTargetMetaclassComponent(FlowComponent[pg_domain]):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self, restricted: list[type]):
        super().__init__('validate-target-metaclass-component')
        self._restricted = restricted

    def execute(self, target: type[pg_domain], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        if not isinstance(target, pg_domain):
            errors.append(f'Target type {type.__name__} must be a pg_domain instance')
        if not isinstance(target, pg_builtin):
            errors.append(f'Target type {type.__name__} must be a pg_builtin instance')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


pgdomain_definition_flow.register_component(
    ValidateTargetMetaclassComponent())


class ExtractCommentDefinitionComponent(FlowComponent[pg_domain]):
    """
    Extract domain comments
    """

    def __init__(self):
        super().__init__('extract-comment-definition-component')

    def execute(self, target: type[pg_domain], accumulator: FlowAccumulator) -> None:
        attr_name: str = f'_{target.__name__}__pg_comment'
        if hasattr(target, attr_name):
            comment: pg_comment = getattr(target, attr_name)()
            accumulator.add_definition('comment', comment.value)


class ExtractCheckDefinitionComponent(FlowComponent[pg_domain]):
    """
    Extract domain check constraints
    """

    def __init__(self):
        super().__init__('extract-check-definition-component')

    def execute(self, target: type[pg_domain], accumulator: FlowAccumulator) -> None:
        attr_name: str = f'_{target.__name__}__pg_check'
        if hasattr(target, attr_name):
            check: pg_check = getattr(target, attr_name)()
            accumulator.add_definition('check', check.predicate.as_str(target.__name__))


pgdomain_definition_flow.register_component(
    ExtractCommentDefinitionComponent())

pgdomain_definition_flow.register_component(
    ExtractCheckDefinitionComponent())

pgdomain_definition_flow.set_critical_component('extract-comment-definition-component')
