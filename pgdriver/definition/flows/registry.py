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
from typing import\
    Any


pg_driver_definition_flow_registry = DefinitionFlowRegistry('pgdriver-definition-flow-registry')

pg_driver_definition_flow_registry.register(pg_table_definition_flow)
pg_driver_definition_flow_registry.register(pg_enum_definition_flow)
pg_driver_definition_flow_registry.register(pg_composite_definition_flow)
pg_driver_definition_flow_registry.register(pg_domain_definition_flow)
pg_driver_definition_flow_registry.register(pg_sequence_definition_flow)


def valid_pg_definition(wrapped_cls: type):
    accumulator: FlowAccumulator = pg_driver_definition_flow_registry.execute_flow(wrapped_cls)
    final_definition: dict[str, Any] = accumulator.get_definition('final')
    for name in final_definition:
        setattr(wrapped_cls, name, final_definition[name])
    return wrapped_cls


__all__ = {
    'valid_pg_definition': valid_pg_definition}
