from pgdriver.definition.flow import\
    FlowAccumulator,\
    DefinitionFlow,\
    FlowComponent
from typing import\
    Any
from .representable import\
    PGRepresentable
from pgdriver.definition.inspection import\
    extract_by_instance_type_from_inherited_classes,\
    identity_generator


pgobject_definition_flow = DefinitionFlow('pgdriver-object-definition-flow', object)


# Aqui tenemos que validar que el type de postgres herede de un type base: pg_domain,
# pg_composite, pg_table, pg_enum, pg_builtin
# no puede heredar de dos types base
class ValidateTypeInheritanceTask(FlowComponent):
    """
    Las clases pueden tener herencia cruzada por ejemplo heredar de un composite y table
    a la vez, esto es ilegal, esta validacion la corremos al momento de definir el 
    core_schema de pydantic para asegurarnos que el PGRepresentable es valido y 
    su definicion univoca
    """

    def __init__(self):
        super().__init__('validate-type-inheritance-task')

    def execute(self, cls: type, accumulator: FlowAccumulator) -> None:
        definition_kinds: set[type] = set()
        for base_class in extract_by_instance_type_from_inherited_classes(cls, PGRepresentable):
            if base_class is PGRepresentable:
                definition_kinds = definition_kinds.union(set(base_class.__orig_bases__))
        if len(definition_kinds) > 1:
            accumulator.errors.append(self.name, ', '.join(definition_kinds))


pgobject_definition_flow.register_component(
    ValidateTypeInheritanceTask())

# pgobject_definition_flow.register(table_validate_type_declaration_stage)

