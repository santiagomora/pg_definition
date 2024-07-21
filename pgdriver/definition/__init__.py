# from typing_extensions import Annotated
# from .base import pg_enum, \
#     pg_text, \
#     pg_float, \
#     pg_json, \
#     pg_bytes, \
#     pg_timestamp, \
#     pg_timestamptz, \
#     pg_date, \
#     pg_time, \
#     pg_timetz, \
#     pg_composite, \
#     pg_bool, \
#     pg_table, \
#     pg_schema, \
#     pg_type, \
#     pg_int, \
#     pg_bigint, \
#     pg_class
# from .constraint import \
#     pg_unique, \
#     pg_primary_key, \
#     pg_foreign_key, \
#     pg_index
# 
# __all__ = [
#     'Annotated',
#     'pg_enum',
#     'pg_text',
#     'pg_float',
#     'pg_json',
#     'pg_bytes',
#     'pg_timestamp',
#     'pg_timestamptz',
#     'pg_date',
#     'pg_time',
#     'pg_timetz',
#     'pg_composite',
#     'pg_bool',
#     'pg_table',
#     'pg_schema',
#     'pg_type',
#     'pg_int',
#     'pg_bigint'
#     'pg_unique',
#     'pg_primary_key',
#     'pg_foreign_key',
#     'pg_index',
#     'pg_default']
from pgdriver.definition.types.table import\
    pgtable_definition_flow
from pgdriver.definition.types.base import\
    pgobject_definition_flow
from .registry import\
    DefinitionFlowRegistry


pgdriver_definition_flow_registry = DefinitionFlowRegistry('pgdriver-definition-flow-registry')
pgdriver_definition_flow_registry.register_definition_flow(pgobject_definition_flow)
pgdriver_definition_flow_registry.register_definition_flow(pgtable_definition_flow)


__all__ = {
    'pgdriver_definition_flow_registry': pgdriver_definition_flow_registry}
