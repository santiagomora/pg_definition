from pgdriver.definition.extraction.functions import\
    extract_module_definition,\
    convert_db_definition_to_module_definition
from pgdriver.migration.backend.functions import\
    extract_db_definition
from deepdiff import\
    DeepDiff
from typing import\
    Any,\
    TypeVar,\
    Generic


T = TypeVar('T')


async def mgr_compare_db_and_module_definition(definition: type) -> DeepDiff:
    module_definition: Any = extract_module_definition(definition)
    db_definition: Any = await extract_db_definition(definition.schema_name, definition.name)
    db_module_adapt: Any = convert_db_definition_to_module_definition(db_definition)
    return DeepDiff(module_definition, db_module_adapt)
