from pgdriver.definition.flows import\
    DefinitionFlowRegistry
from pgdriver.definition.flows.table import\
    pgtable_definition_flow
from pgdriver.definition.flows.composite import\
    pgcomposite_definition_flow
from pgdriver.definition.flows.domain import\
    pgdomain_definition_flow
from pgdriver.definition.flows.enum import\
    pgenum_definition_flow
from pgdriver.definition.flows import\
    FlowAccumulator
from pgdriver.definition.inspection import\
    extract_by_instance_type_from_inherited_classes


pgdriver_definition_flow_registry = DefinitionFlowRegistry('pgdriver-definition-flow-registry')

pgdriver_definition_flow_registry.register(pgtable_definition_flow)
pgdriver_definition_flow_registry.register(pgenum_definition_flow)
pgdriver_definition_flow_registry.register(pgcomposite_definition_flow)
pgdriver_definition_flow_registry.register(pgdomain_definition_flow)


def valid_pg_definition(wrapped_cls: type):
    accumulator: FlowAccumulator = pgdriver_definition_flow_registry.execute_flow(wrapped_cls)
    print(accumulator.get_definition('final'))
    bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)
    return type(wrapped_cls.__name__, bases, accumulator.get_definition('final'))


__all__ = {
    'pgdriver_definition_flow_registry': pgdriver_definition_flow_registry,
    'valid_pg_definition': valid_pg_definition}
