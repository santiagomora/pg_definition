from pgdriver.definition.flows import\
    DefinitionFlowRegistry
from pgdriver.definition.flows.table import\
    pg_table_definition_flow
from pgdriver.definition.flows.composite import\
    pg_composite_definition_flow
from pgdriver.definition.flows.domain import\
    pg_domain_definition_flow
from pgdriver.definition.flows.enum import\
    pg_enum_definition_flow
from pgdriver.definition.flows.sequence import\
    pg_sequence_definition_flow
from pgdriver.definition.flows import\
    FlowAccumulator
from pgdriver.definition.inspection import\
    extract_by_instance_type_from_inherited_classes


pg_driver_definition_flow_registry = DefinitionFlowRegistry('pgdriver-definition-flow-registry')

pg_driver_definition_flow_registry.register(pg_table_definition_flow)
pg_driver_definition_flow_registry.register(pg_enum_definition_flow)
pg_driver_definition_flow_registry.register(pg_composite_definition_flow)
pg_driver_definition_flow_registry.register(pg_domain_definition_flow)
pg_driver_definition_flow_registry.register(pg_sequence_definition_flow)


def valid_pg_definition(wrapped_cls: type):
    accumulator: FlowAccumulator = pg_driver_definition_flow_registry.execute_flow(wrapped_cls)
    bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)
    return type(wrapped_cls.__name__, bases, accumulator.get_definition('final') | wrapped_cls.__dict__)


__all__ = {
    'valid_pg_definition': valid_pg_definition}
