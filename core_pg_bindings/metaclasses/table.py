from typing import\
    Type,\
    Generic,\
    Optional,\
    TypeVar,\
    Any
from dataclasses import\
    dataclass
from pydantic_core import\
    core_schema
from pydantic import\
    GetCoreSchemaHandler,\
    ValidationInfo
from pydantic.fields import\
    FieldInfo
from ..common.flow import\
    execute_definition_flow,\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator,\
    NodeException,\
    RootDefinitionFlowNode,\
    DefinitionFlowBuilder
from enum import\
    Enum
from .enums import\
    enum
from .builtin import\
    builtin,\
    compound
from ..common.inspection import\
    extract_definition_fields
from ..objects.sequence import\
    sequence
from ..objects.comment import\
    add_comment,\
    add_field_comment
import pydantic_core
import copy
import functools
from pydantic import\
    create_model
import core_types as bt
import inspect
from typing_extensions import\
    Self


# KNOWN BUGS
# BUG: if two parent table share the same value of the same type, and each one sets a different default value, then postgres will raise a conflict error, breaking the transaction. wont be implemented in this first version.


__all__ = ['table']


table_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('table-definition-flow')
table_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(table_definition_flow_root)


class TableOperandDefinitionContext(bt.OperandDefinitionContext):
    @classmethod
    def parse_field(cls, field_instance: bt.field) -> str:
        return f'{field_instance._fieldname}'

    @classmethod
    def parse_this(cls, this_instance: bt.this) -> str:
        if this_instance._fieldname is None:
            raise ValueError(f'Operand {repr(this_instance)} definition not correctly propagated.')
        return f'{this_instance._fieldname}'


class table(compound):
    class index_type(Enum):
        BTREE = 'btree'
        HASH = 'hash'
        GIN = 'gin'
        BRIN = 'brin'
        GIST = 'gist'
        SPGIST = 'spgist'

    class foreign_key_action(Enum):
        SET_NULL = 'SET NULL'
        SET_DEFAULT = 'SET DEFAULT'
        RESTRICT = 'RESTRICT'
        NO_ACTION = 'NO ACTION'
        CASCADE = 'CASCADE'

    class add_comment(add_comment):
        pass

    class add_column_comment(add_field_comment):
        def __init__(
            self, *, column: str, value: str
        ):
            return super().__init__(field_name=column, value=value, accessor='columns')

    class set_default(compound.set_default):
        def __init__(
            self, *, column: str, default: Any
        ) -> None:
            return super().__init__(field=column, value=default)

        def __call__(self, target: type) -> type:
            target._postgres_definition['columns'][self._field_name]['default'] = self._default
            return super().__call__(target)

    class set_check_constraint(compound.set_constraint):
        def __init__(
            self, *, column: str, name: str, constraint: bt.LogicOperand
        ) -> None:
            constraint.name = name
            return super().__init__(
                field_name=column, constraint=constraint, accessor='columns'
            )

    class primary_key:
        def __init__(
            self, *, name: str,  columns: tuple[str, ...]
        ) -> None:
            self.primary_key: dict[str, Any] = {
                'name': name,
                'columns': columns}

        def __call__(self, target: type):
            assert isinstance(target, table)
            definition = target._postgres_definition
            invalid_columns: set[str] = set(self.primary_key['columns']) - set(target.model_fields.keys())
            if definition['primary_key'] is not None:
                raise TypeError(f'Table "{target}" already has a primary key')
            if len(invalid_columns) > 0:
                raise TypeError(f'Invalid primary key definition, columns "{invalid_columns}" not present in table definition')
            definition['primary_key'] = self.primary_key
            return target

    class foreign_key:
        def __init__(
            self, *, name: str,  columns: tuple[str, ...], references: type['table'],
            referenced_columns: tuple[str, ...],
            on_update: Optional['table.foreign_key_action'] = None,
            on_delete: Optional['table.foreign_key_action'] = None
        ) -> None:
            if references is not Self and not isinstance(references, table):
                raise TypeError(f'{table} must be of type table')
            if len(columns) != len(referenced_columns):
                raise TypeError(f'must declare as many columns as referenced columns')
            if len(columns) == 0:
                raise TypeError(f'must declare columns')
            self.foreign_key: dict[str, Any] = {
                'name': name,
                'columns': columns,
                'references': references,
                'referenced_columns': referenced_columns,
                'on_update': table.foreign_key_action.NO_ACTION if on_update is None else on_update,
                'on_delete': table.foreign_key_action.NO_ACTION if on_delete is None else on_delete }

        def _extract_references_constraints(
            self, constraint_names: tuple[str, ...]
        ) -> list[dict[str, Any]]:
            references_pg_def: Optional[dict[str, Any]] = self.foreign_key['references']._postgres_definition
            res: dict[str, Any] = {}
            for name in constraint_names:
                if references_pg_def[name] is not None:
                    if 'name' in references_pg_def[name]:
                        res[references_pg_def[name]['name']] = references_pg_def[name]
                    else:
                        res |= references_pg_def[name]
            return res

        def _check_for_references_constraints(
            self, *constraint_names: tuple[str, ...]
        ) -> list[str]:
            fk: dict[str, Any] = self.foreign_key
            constraints: list[dict[str, Any]] = self._extract_references_constraints(constraint_names)
            referenced_columns= set(fk['referenced_columns'])
            if len(constraints) == 0 or not any([len(referenced_columns - set(const['columns'])) == 0 for _, const in constraints.items()]):
                raise TypeError(f'Foreign key "{fk["name"]}" error: Other class "{fk["references"]}" must define any {constraint_names} constraint over referenced columns {fk["referenced_columns"]}')

        def _check_references_column_types(
            self, target: type['table']
        ) -> list[str]:
            fk: dict[str, Any] = self.foreign_key
            for ix in range(0, len(fk['columns'])):
                column: dict = target._postgres_definition['columns'][fk['columns'][ix]]
                if fk['referenced_columns'][ix] not in fk['references']._postgres_definition['columns']:
                    raise TypeError(f'Foreign key column "{fk["referenced_columns"][ix]}" must exist in "{self.foreign_key['references']}" definition')
                other_column_tp: type = fk['references']._postgres_definition['columns'][fk['referenced_columns'][ix]]['type']
                column_tp: type = column['type']
                if column_tp != other_column_tp:
                    raise TypeError(f'Foreign key column "{column['name']}" type must match with "{fk['referenced_columns'][ix]}" in {fk["name"]} definition')

        def _check_columns_not_constrained_by_foreign_key_definition(self, target: type):
            constrained_columns = set()
            for fk_name, fk_def in target._postgres_definition['foreign_keys'].items():
                constrained_columns = constrained_columns.union(set(fk_def['columns']))
            already_constrained = set(self.foreign_key['columns']).intersection(constrained_columns)
            if len(already_constrained) > 0:
                raise TypeError(f'Columns "{already_constrained}" already constrained by a foreign key definition')

        def __call__(self, target: type):
            if self.foreign_key['references'] is Self:
                self.foreign_key['references'] = target
            assert isinstance(target, table)
            definition = target._postgres_definition
            if self.foreign_key['name'] in definition['foreign_keys']:
                raise TypeError(f"Foreign key \"{self.foreign_key["name"]}\" already defined")
            invalid_columns: set[str] = set(self.foreign_key['columns']) - set(target._postgres_definition['columns'].keys())
            if len(invalid_columns) > 0:
                raise TypeError(f'Invalid foreign key definition, columns "{invalid_columns}" not present in table definition')
            self._check_references_column_types(target)
            self._check_for_references_constraints('unique_constraints', 'primary_key', 'indexes')
            self._check_columns_not_constrained_by_foreign_key_definition(target)
            definition['foreign_keys'][self.foreign_key['name']] = self.foreign_key
            return target

    class unique_constraint:
        def __init__(self, name: str,  columns: tuple[str, ...]) -> None:
            assert len(columns) > 0
            self.unique_constraint: dict[str, Any] = {
                'name': name,
                'columns': columns}

        def __call__(self, target: type):
            assert isinstance(target, table)
            definition = target._postgres_definition
            if self.unique_constraint['name'] in definition['unique_constraints']:
                raise TypeError(f"Unique constraint \"{self.unique_constraint["name"]}\" already defined")
            invalid_columns: set[str] = set(self.unique_constraint['columns']) - set(target._postgres_definition['columns'].keys())
            if len(invalid_columns) > 0:
                raise TypeError(f'Invalid unique constraint definition, columns "{invalid_columns}" not present in table definition')
            definition['unique_constraints'][self.unique_constraint['name']] = self.unique_constraint
            return target

    class index:
        def __init__(
            self, *, name: str, columns: tuple[str, ...],
            index_type: Optional['table.index_type'] = None, unique: bool = False,
        ) -> None:
            self.index: dict[str, Any] = {
                'name': name,
                'type': table.index_type.BTREE if index_type is None else index_type,
                'unique': unique,
                'columns': columns}

        def __call__(self, target: type):
            assert isinstance(target, table)
            definition = target._postgres_definition
            if self.index['name'] in definition['indexes']:
                raise TypeError(f"Index \"{self.index["name"]}\" already defined")
            invalid_columns: set[str] = set(self.index['columns']) - set(target._postgres_definition['columns'].keys())
            if len(invalid_columns) > 0:
                raise TypeError(f'Invalid index definition, columns "{invalid_columns}" not present in table definition')
            definition['indexes'][self.index['name']] = self.index
            return target

    class serial:
        def __init__(
            self, *, column: str, sequence: type[sequence]
        ) -> None:
            self.column = column
            self.seq = sequence

        def __call__(self, target: type):
            assert isinstance(target, table)
            definition = target._postgres_definition
            assert self.column in definition['columns']
            assert definition['columns'][self.column]['default'] is bt.Undefined
            definition['columns'][self.column]['default'] = sequence.nextval(seq=self.seq)
            if definition['columns'][self.column]['type'] != self.seq._postgres_definition['base_type']:
                raise TypeError('Sequence type must match annotated type')
            return target

    def __new__(
        cls, clsname, clsbases, namespace
    ) -> type:
        rettype: type = super().__new__(
            cls, clsname, clsbases, namespace
        )
        execute_definition_flow(rettype, table_definition_flow_root)
        return rettype

    def definition_context(self) -> type[bt.OperandDefinitionContext]:
        return TableOperandDefinitionContext


class _TableExtractColumnsNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('table-extract-column-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de columna
        columns: dict[str, dict[str, Any]] = {}
        for name, info in extract_definition_fields(target):
            columns[name] = {
                'name': name,
                'required': info.is_required(),
                'type': info.annotation,
                'comment': None,
                'check': None,
                'default': info.default}
        accumulator.add_definition('columns', columns)


class _TableStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('table-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = dict()
        definition['schema'] = inspect.getmodule(target)
        definition['type'] = target
        definition['bases'] = tuple([base.get_py_cls(base.qualified_name) for base in target._cpp_bases])
        definition['comment'] = None
        definition['columns'] = accumulator.get_definition('columns', 'extraction')
        definition['primary_key'] = None
        definition['foreign_keys'] = {}
        definition['unique_constraints'] = {}
        definition['indexes'] = {}
        definition['kind'] = 'table'
        # definition['check'] = saccumulator.get_definition('check_constraints', 'extraction')
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('table-extract-column-definition-node', )


table_flow_builder\
    .at_work_path('extraction')\
        .add_node(_TableExtractColumnsNode)\
    .at_work_path('')\
        .add_node(_TableStoreFinalDefinitionNode).critical()

