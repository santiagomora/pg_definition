from pgdriver.definition.base import\
    FlowAccumulator,\
    FlowComponentException,\
    TypeInstanceDefinitionFlow,\
    FlowComponent
from pgdriver.definition.tools import\
    pg_domain,\
    pg_builtin
from pgdriver.definition.common import\
    CommonExtractCheckDefinitionComponent,\
    CommonExtractCommentDefinitionComponent


class DomainValidateTargetMetaclassComponent(FlowComponent[pg_domain]):
    """
    target type must be an instance of pg_domain and pg_builtin
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

    def get_dependencies(self) -> tuple[str]:
        return tuple()


class DomainExtractCheckDefinitionComponent(CommonExtractCheckDefinitionComponent[pg_domain]):
    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-check-definition-component')


class DomainExtractCommentDefinitionComponent(CommonExtractCommentDefinitionComponent[pg_domain]):
    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-comment-definition-component')


class DomainStoreCheckDefinitionComponent(CommonExtractCheckDefinitionComponent[pg_domain]):
    def get_dependencies(self) -> tuple[str]:
        return tuple('store-target-metaclass-component')


class DomainStoreCommentDefinitionComponent(CommonExtractCommentDefinitionComponent[pg_domain]):
    def get_dependencies(self) -> tuple[str]:
        return tuple('store-target-metaclass-component')


class DomainDefinitionFlow(TypeInstanceDefinitionFlow[pg_domain]):
    def __init__(self):
        super().__init__('pgdriver-domain-definition-flow')


pgdomain_definition_flow: DomainDefinitionFlow = DomainDefinitionFlow()

with pgdomain_definition_flow.at_path('validation') as flow:
    flow.register(DomainValidateTargetMetaclassComponent())

    with pgdomain_definition_flow.at_path('extraction') as flow:
        flow.register(DomainExtractCommentDefinitionComponent().critical())
        flow.register(DomainExtractCheckDefinitionComponent())

with pgdomain_definition_flow.at_path('final') as flow:
    flow.register(DomainStoreCommentDefinitionComponent().critical())
    flow.register(DomainStoreCheckDefinitionComponent())

__all__ = {'pgdomain_definition_flow': pgdomain_definition_flow}
