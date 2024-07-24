from pgdriver.definition.base import\
    FlowAccumulator,\
    FlowComponentException,\
    FlowComponent
from pgdriver.definition.tools import\
    pg_domain,\
    pg_builtin


class DomainValidateTargetMetaclassComponent(FlowComponent[pg_domain]):
    """
    target type must be an instance of pg_domain and pg_builtin
    """

    def __init__(self, restricted: list[type]):
        super().__init__('domain-validate-target-metaclass-component')
        self._restricted = restricted

    def execute(self, target: type[pg_domain], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        if not isinstance(target, pg_domain):
            errors.append(f'Target type {type.__name__} must be a pg_domain instance')
        if not isinstance(target, pg_builtin):
            errors.append(f'Target type {type.__name__} must be a pg_builtin instance')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)
