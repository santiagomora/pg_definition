from pgdriver.definition.flows import\
    FlowAccumulator,\
    FlowComponentException,\
    TypeInstanceDefinitionFlow,\
    FlowComponent
from pgdriver.definition.build import\
    pg_domain,\
    pg_builtin,\
    pg_composite


class DomainValidateTargetMetaclassComponent(FlowComponent[pg_domain]):
    """
    target type must be an instance of pg_domain and pg_builtin
    """

    def __init__(self):
        super().__init__('validate-target-metaclass-component')

    def execute(self, target: type[pg_domain], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        if not isinstance(target, pg_domain):
            errors.append(f'Target type {type} must be a pg_domain instance')
        if not isinstance(target, pg_builtin):
            errors.append(f'Target type {type} must be a pg_builtin instance')
        if not isinstance(target, pg_composite):
            errors.append(f'Target type {type} must be a pg_composite instance')
        if len(errors) > 0:
            raise FlowComponentException(self.name, [' or '.join(errors)])


class DomainDefinitionFlow(TypeInstanceDefinitionFlow[pg_domain]):
    def __init__(self):
        super().__init__('pgdriver-domain-definition-flow')


pg_domain_definition_flow: DomainDefinitionFlow = DomainDefinitionFlow()

with pg_domain_definition_flow.at_work_path('validation') as flow:
    flow.register(DomainValidateTargetMetaclassComponent())

__all__ = {'pg_domain_definition_flow': pg_domain_definition_flow}
