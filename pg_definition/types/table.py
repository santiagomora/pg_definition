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
from ..common.node import\
    ModelValidateUniqueMetadataTypesNode,\
    ModelDiscardMetaInstancesFromInheritedFieldsNode,\
    ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode,\
    CommonValidateRestrictedMetadataTypesNode,\
    CommonValidateFieldsBaseTypeNode
from enum import\
    Enum
from .enums import\
    enum
from .builtin import\
    builtin,\
    compound
from ..common.inspection import\
    extract_inherited_fields,\
    extract_by_instance_type_from_model_fields_info,\
    aggregate,\
    tuple_accumulator,\
    key_by,\
    extract_first_instance_from_field_metadata,\
    extract_definition_fields
from ..objects.check import\
    check
from ..objects.comment import\
    comment
from ..objects.sequence import\
    sequence,\
    nextval
import pydantic_core
import copy
import functools
from pydantic import\
    create_model
import base_types as bt


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


# KNOWN BUGS
# BUG: if two parent table share the same value of the same type, and each one sets a different default value, then postgres will raise a conflict error, breaking the transaction. wont be implemented in this first version.


__all__ = ['table', 'primary_key', 'foreign_key', 'serial', 'unique_constraint', 'index', 'index_type', 'foreign_key_action']


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
    def __new__(
        cls, clsname, clsbases, namespace
    ) -> type:
        rettype: type = super().__new__(
            cls, clsname, clsbases, namespace,
            inheritance_policy=bt.InheritancePolicy.DISALLOW
        )
        execute_definition_flow(rettype, table_definition_flow_root)
        return rettype

    def definition_context(self) -> type[bt.OperandDefinitionContext]:
        return TableOperandDefinitionContext


# class _TableValidateExistingColumnsNode(SingleChoiceDefinitionFlowNode):
#     """
#     We must ensure that target definition has fields
#     """
# 
#     def __init__(self):
#         super().__init__('table-validate-existing-columns-node')
# 
#     def execute(self, target: type, accumulator: FlowAccumulator) -> None:
#         if len(target.model_fields.keys()) <= 0:
#             raise NodeException(self.name, [f'Class {target} must define columns.'])


# class _TableValidateMutuallyExclusiveMetadataNode(SingleChoiceDefinitionFlowNode):
#     """
#     We must ensure that target definition fields has no two metadata instances indicated by mutually_exclusive pairs at the same time.
#     """
# 
#     def __init__(self):
#         super().__init__('table-validate-mutually-exclusive-metadata-node')
#         self.mutually_exclusive: list[tuple[type, type]] = []
# 
#     def execute(self, target: type, accumulator: FlowAccumulator) -> None:
#         errors: list[str] = []
#         for field, info in target.model_fields.items():
#             for tp1, tp2 in self.mutually_exclusive:
#                 tp1inst: Optional[Any] = extract_first_instance_from_field_metadata(info, tp1)
#                 tp2inst: Optional[Any] = extract_first_instance_from_field_metadata(info, tp2)
#                 if tp1inst is not None and tp2inst is not None:
#                     errors.append(f'Field {field} described by two mutually exclusive metadata instances: {repr(tp2inst)} and {repr(tp1inst)}')
#         if len(errors) > 0:
#             raise NodeException(self.name, errors)


class _TableValidateSameTypeMetaInstancesHaveDifferentNamesNode(ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode):
    def __init__(self):
        super().__init__('table-validate-same-type-meta-instances-have-different-names-node',
                         types=[check])


class _TableValidateRestrictedMetadataTypesNode(CommonValidateRestrictedMetadataTypesNode):
    def __init__(self):
        super().__init__('table-validate-restricted-metadata-types-node',
                         types=[check, comment])


class _TableValidateUniqueMetadataTypesNode(ModelValidateUniqueMetadataTypesNode):
    def __init__(self):
        super().__init__('table-validate-unique-metadata-types-node',
                         types=[comment])


class _TableValidateFieldsBaseTypeNode(CommonValidateFieldsBaseTypeNode):
    def __init__(self):
        super().__init__('table-validate-fields-base-type-node',
                         type_subclass=[],
                         type_instance=[enum, builtin, compound])


class _TableDependsOnValidationNodes:
    def get_dependencies(self) -> tuple[str]:
        return ('table-validate-mutually-exclusive-metadata-node',
                'table-validate-restricted-metadata-types-node',
                'table-validate-unique-metadata-types-node',
                'table-validate-same-type-meta-instances-have-different-names-node',
                'table-validate-fields-base-type-node',
                'table-merge-inherited-fields-node',
                'table-validate-existing-columns-node')


class _TableExtractCheckConstraintsNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('table-extract-check-constraints-node')
        self._context = TableOperandDefinitionContext

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        pass
        # checks: dict[str, check] = {}
        # for field, ck in extract_by_instance_type_from_model_fields_info(target, check):
        #     ck.predicate.propagate_definition(target.model_fields[field].annotation, field, self._context)
        #     ck.name = f'{target.__name__}_{ck.name}'
        #     if ck.name not in checks:
        #         checks[ck.name] = ck
        #     else:
        #         checks[ck.name].predicate = checks[ck.name].predicate & ck.predicate
        # accumulator.add_definition('check_constraints', checks if checks != {} else None)


class _TableExtractColumnsNode(SingleChoiceDefinitionFlowNode, _TableDependsOnValidationNodes):
    def __init__(self):
        super().__init__('table-extract-column-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de columna
        columns: dict[str, dict[str, Any]] = {}
        for name, info in extract_definition_fields(target):
            tp: type = info.annotation
            col_data: dict[str, Any] = {
                'name': name,
                'required': info.is_required(),
                'type': tp}
            comment_inst: Optional[comment] = extract_first_instance_from_field_metadata(info, comment)
            col_data['comment'] = comment_inst
            # if not info.is_required():
            #     if isinstance(info.default, bt.Operand):
            #         col_data['default'] = info.default
            #         info.default.propagate_definition(tp, name, TableOperandDefinitionContext)
            #         # cant have default_factory and default set at the same time
            #         default_factory = copy.deepcopy(info.default.value)
            #         info.default_factory = lambda value: tp(default_factory(value))
            #         info.default = pydantic_core._pydantic_core.PydanticUndefined
            #     else:
            #         col_data['default'] = tp(info.default) if info.default is not None and not isinstance(info.default, tp) else None
            #         info.default = col_data['default']
            columns[name] = col_data
        target.model.model_rebuild(force=True)
        accumulator.add_definition('columns', columns)


class _TableDiscardMetaInstancesFromInheritedFieldsNode(ModelDiscardMetaInstancesFromInheritedFieldsNode, _TableDependsOnValidationNodes):
    def __init__(self):
        super().__init__('table-discard-meta-instances-from-inherited-fields-node')


class _TableStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('table-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = dict()
        definition['schema'] = None
        definition['type'] = target
        definition['bases'] = None
        definition['comment'] = None
        definition['columns'] = accumulator.get_definition('columns', 'extraction')
        definition['primary_key'] = None
        definition['foreign_keys'] = {}
        definition['unique_constraints'] = {}
        definition['indexes'] = {}
        definition['kind'] = 'table'
        definition['check'] = accumulator.get_definition('check_constraints', 'extraction')
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('table-extract-column-definition-node',
                'table-extract-check-constraints-node',
                'table-discard-meta-instances-from-inherited-fields-node')


# .add_node(_TableValidateMutuallyExclusiveMetadataNode)\
# .add_node(_TableValidateExistingColumnsNode)\
table_flow_builder\
    .at_work_path('validation')\
        .add_node(_TableValidateSameTypeMetaInstancesHaveDifferentNamesNode)\
        .add_node(_TableValidateRestrictedMetadataTypesNode)\
        .add_node(_TableValidateUniqueMetadataTypesNode)\
        .add_node(_TableValidateFieldsBaseTypeNode)\
    .at_work_path('extraction')\
        .add_node(_TableExtractCheckConstraintsNode)\
        .add_node(_TableExtractColumnsNode)\
        .add_node(_TableDiscardMetaInstancesFromInheritedFieldsNode)\
    .at_work_path('')\
        .add_node(_TableStoreFinalDefinitionNode).critical()


class primary_key:
    def __init__(self, *, name: str,  columns: tuple[str, ...]) -> None:
        self.primary_key: dict[str, Any] = {
            'name': name,
            'columns': columns}

    def __call__(self, target: type):
        assert isinstance(target, table)
        definition = getattr(target, '__pg_definition')()
        invalid_columns: set[str] = set(self.primary_key['columns']) - set(target.model_fields.keys())
        assert definition['primary_key'] is None
        if len(invalid_columns) > 0:
            raise TypeError(f'Invalid primary key definition, columns "{invalid_columns}" not present in table definition')
        definition['primary_key'] = self.primary_key
        return target


# TODO changes:
# references -> references
# referenced_columns -> referenced_columns
class foreign_key:
    def __init__(
        self, *, name: str,  columns: tuple[str, ...], references: type[table],
        referenced_columns: tuple[str, ...],
        on_update: foreign_key_action = foreign_key_action.NO_ACTION,
        on_delete: foreign_key_action = foreign_key_action.NO_ACTION
    ) -> None:
        assert isinstance(references, table)
        assert len(columns) == len(referenced_columns)
        assert len(columns) > 0
        self.foreign_key: dict[str, Any] = {
            'name': name,
            'columns': columns,
            'references': references,
            'referenced_columns': referenced_columns,
            'on_update': on_update,
            'on_delete': on_delete}

    def _extract_references_constraints(
        self, constraint_names: tuple[str, ...]
    ) -> list[dict[str, Any]]:
        references_pg_def: Optional[dict[str, Any]] = getattr(self.foreign_key['references'], '__pg_definition')()
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
        self, target: type[table]
    ) -> list[str]:
        fk: dict[str, Any] = self.foreign_key
        for ix in range(0, len(self.foreign_key['columns'])):
            column: FieldInfo = target.model_fields[fk['columns'][ix]]
            if fk['referenced_columns'][ix] not in fk['references'].model_fields:
                raise TypeError(f'Foreign key column "{fk["referenced_columns"][ix]}" must exist in <class \'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test2\'> definition')
            other_column: FieldInfo = fk['references'].model_fields[fk['referenced_columns'][ix]]
            if column.annotation != other_column.annotation:
                raise TypeError(f'Foreign key column "{fk["columns"][ix]}" type must match with "{fk['referenced_columns'][ix]}" in {fk["references"]} definition')

    def __call__(self, target: type):
        assert isinstance(target, table)
        definition = getattr(target, '__pg_definition')()
        assert self.foreign_key['name'] not in definition['foreign_keys']
        invalid_columns: set[str] = set(self.foreign_key['columns']) - set(target.model_fields.keys())
        if len(invalid_columns) > 0:
            raise TypeError(f'Invalid foreign key definition, columns "{invalid_columns}" not present in table definition')
        self._check_references_column_types(target)
        self._check_for_references_constraints('unique_constraints', 'primary_key', 'indexes')
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
        definition = getattr(target, '__pg_definition')()
        assert self.unique_constraint['name'] not in definition['unique_constraints']
        invalid_columns: set[str] = set(self.unique_constraint['columns']) - set(target.model_fields.keys())
        if len(invalid_columns) > 0:
            raise TypeError(f'Invalid unique constraint definition, columns "{invalid_columns}" not present in table definition')
        definition['unique_constraints'][self.unique_constraint['name']] = self.unique_constraint
        return target


class index:
    def __init__(
        self, *, name: str, columns: tuple[str, ...],
        type: index_type = index_type.BTREE, unique: bool = False,
    ) -> None:
        self.index: dict[str, Any] = {
            'name': name,
            'type': type,
            'unique': unique,
            'columns': columns}

    def __call__(self, target: type):
        assert isinstance(target, table)
        definition = getattr(target, '__pg_definition')()
        assert self.index['name'] not in definition['indexes']
        invalid_columns: set[str] = set(self.index['columns']) - set(target.model_fields.keys())
        if len(invalid_columns) > 0:
            raise TypeError(f'Invalid index definition, columns "{invalid_columns}" not present in table definition')
        definition['indexes'][self.index['name']] = self.index
        return target


class serial:
    def __init__(
        self, *, column: str, sequence: sequence
    ) -> None:
        self.column = column
        self.seq = sequence

    def __call__(self, target: type):
        assert isinstance(target, table)
        definition = getattr(target, '__pg_definition')()
        assert self.column in definition['columns']
        assert 'default' not in definition['columns'][self.column]
        definition['columns'][self.column]['default'] = nextval(seq=self.seq)
        if not issubclass(definition['columns'][self.column]['type'], getattr(self.seq, '__pg_definition')()['base_type']):
            raise TypeError('Sequence type must match annotated type')
        return target


class inherits(bt.inherits):
    def __call__(self, target: type[table]) -> type[table]:
        assert isinstance(target, table)
        return bt.inherits.__call__(self, target)
