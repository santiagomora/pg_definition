from pgdriver.definition.extraction.base import\
    pg_composite_definition,\
    pg_table_definition,\
    pg_enum_definition,\
    pg_domain_definition,\
    pg_sequence_definition
from pgdriver.definition.build import\
    pg_composite,\
    pg_table,\
    pg_enum,\
    pg_domain,\
    pg_sequence
from pgdriver.definition.inspection import\
    execute_classmethod
from typing import\
    Any


def get_composite_definition(composite_def: type[pg_composite]) -> pg_composite_definition:
    """
    Precondition: composite_def is a valid pg definition, this means the definition
    flow has ben executed over composite_def
    """
    definition: dict[str, Any] = dict()
    definition['name'] = composite_def.__name__
    definition['schema_name'] = execute_classmethod(composite_def, '__pg_schema_name')
    definition['attributes'] = execute_classmethod(composite_def, '__pg_attributes')
    definition['comment'] = execute_classmethod(composite_def, '__pg_comment')
    return pg_composite_definition(**definition)


def get_table_definition(table_def: type[pg_table]) -> pg_table_definition:
    """
    Precondition: table_def is a valid pg definition, this means the definition
    flow has ben executed over table_def
    """
    definition: dict[str, Any] = dict()
    definition['name'] = table_def.__name__
    definition['schema_name'] = execute_classmethod(table_def, '__pg_schema_name')
    definition['base_classes'] = execute_classmethod(table_def, '__pg_base_classes')
    definition['comment'] = execute_classmethod(table_def, '__pg_comment')
    definition['columns'] = execute_classmethod(table_def, '__pg_columns')
    definition['foreign_keys'] = execute_classmethod(table_def, '__pg_foreign_keys')
    definition['indexes'] = execute_classmethod(table_def, '__pg_indexes')
    definition['primary_key'] = execute_classmethod(table_def, '__pg_primary_key')
    return pg_table_definition(**definition)


def get_enum_definition(enum_def: type[pg_enum]) -> pg_enum_definition:
    """
    Precondition: enum_def is a valid pg definition, this means the definition
    flow has ben executed over enum_def
    """
    definition: dict[str, Any] = dict()
    definition['name'] = enum_def.__name__
    definition['schema_name'] = execute_classmethod(enum_def, '__pg_schema_name')
    definition['values'] = execute_classmethod(enum_def, '__pg_schema_name')
    definition['comment'] = execute_classmethod(enum_def, '__pg_comment')
    return pg_enum_definition(**definition)


def get_domain_definition(domain_def: type[pg_domain]) -> pg_domain_definition:
    """
    Precondition: domain_def is a valid pg definition, this means the definition
    flow has ben executed over domain_def
    """
    definition: dict[str, Any] = dict()
    definition['name'] = domain_def.__name__
    definition['schema_name'] = execute_classmethod(domain_def, '__pg_schema_name')
    definition['comment']: execute_classmethod(domain_def, '__pg_comment')
    definition['check_constraint']: execute_classmethod(domain_def, '__pg_comment')
    definition['base_type_name']: execute_classmethod(domain_def, '__pg_base_type_name')
    return pg_domain_definition(**definition)


def extract_sequence_definition(sequence_def: type[pg_sequence]) -> pg_sequence_definition:
    """
    Precondition: sequence_def is a valid pg definition, this means the definition
    flow has ben executed over sequence_def
    """
    definition: dict[str, Any] = dict()
    definition['name'] = execute_classmethod(sequence_def, '__pg_name')
    definition['schema_name'] = execute_classmethod(sequence_def, '__pg_schema_name')
    definition['comment'] = execute_classmethod(sequence_def, '__pg_comment')
    definition['base_type_name'] = execute_classmethod(sequence_def, '__pg_base_type_name')
    definition['max_value'] = execute_classmethod(sequence_def, '__pg_max_value')
    definition['min_value'] = execute_classmethod(sequence_def, '__pg_min_value')
    return pg_sequence_definition(**definition)


def extract_module_definition(pg_type: type) -> Any:
    if issubclass(pg_type, pg_composite):
        return extract_sequence_definition(pg_type)
    elif issubclass(pg_type, pg_table):
        return extract_sequence_definition(pg_type)
    elif issubclass(pg_type, pg_enum):
        return extract_sequence_definition(pg_type)
    elif isinstance(pg_type, pg_domain):
        return extract_sequence_definition(pg_type)
    elif isinstance(pg_type, pg_sequence):
        return extract_sequence_definition(pg_type)
    raise Exception('Type is not a postgres type')
