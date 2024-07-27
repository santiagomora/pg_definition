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


pgdriver_definition_flow_registry = DefinitionFlowRegistry('pgdriver-definition-flow-registry')

pgdriver_definition_flow_registry.register(pgtable_definition_flow)
pgdriver_definition_flow_registry.register(pgenum_definition_flow)
pgdriver_definition_flow_registry.register(pgcomposite_definition_flow)
pgdriver_definition_flow_registry.register(pgdomain_definition_flow)


__all__ = {
    'pgdriver_definition_flow_registry': pgdriver_definition_flow_registry}
