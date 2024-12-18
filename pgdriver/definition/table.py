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
from .common.flow import\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator,\
    NodeException,\
    DefinitionFlowBuilder
from .common.model import\
    table,\
    composite,\
    table_definition_flow_root,\
    ModelValidateUniqueMetadataTypesNode,\
    ModelDiscardMetaInstancesFromInheritedFieldsNode,\
    ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode
from .common.node import\
    CommonValidateRestrictedMetadataTypesNode,\
    CommonValidateFieldsBaseTypeNode
from .enums import\
    enums
from .builtin import\
    builtin
from .common.inspection import\
    extract_by_instance_type_from_model_fields_info,\
    aggregate,\
    tuple_accumulator,\
    key_by,\
    extract_first_instance_from_field_metadata,\
    extract_definition_fields,\
    is_optional,\
    extract_type
from .meta import\
    meta,\
    OperandDefinitionContext
from pydantic import\
    BaseModel
from enum import\
    Enum


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


__all__ = ['table', 'primary_key', 'foreign_key', 'unique_constraint', 'index', 'index_type', 'foreign_key_action']


table_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(table_definition_flow_root)


class _TableValidateConsistentBaseClassesNode(SingleChoiceDefinitionFlowNode):
    """
    We must ensure that target definition inherits from classes with the same 
    base class. Also we must validate that base classes columns/fields wont
    collide between them.
    """

    def __init__(self):
        super().__init__('table-validate-consistent-base-classes-node')

    def add_field_types(self, from_cls: type, acc: Optional[dict[str, type]] = None) -> dict[str, set[type]]:
        acc = {} if acc is None else acc
        for field, info in from_cls.model_fields.items():
            fset: set[type] = acc.get(field, set())
            fset.add(info.annotation)
            acc[field] = fset
        return acc

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        field_types: dict[str, set[type]] = dict()
        has_more_than_one_base: bool = len(target.__bases__) > 1
        field_types = self.add_field_types(target, None)
        for base_class in target.__bases__:
            if not issubclass(base_class, table):
                errors.append(f'Inherited class {base_class} must be a subclass of {table}')
                continue
            elif has_more_than_one_base and base_class == table:
                errors.append(f'Cant define {table} as base class if {target} is set to inherit more than one base class')
            field_types = self.add_field_types(base_class, field_types)
        for field in field_types:
            if len(field_types[field]) > 1:
                base_cls_str: str = ', '.join([str(f) for f in field_types[field]])
                errors.append(f'Field {field} type conflict. Declared in multiple base classes: {base_cls_str}')
        if len(errors) > 0:
            raise NodeException(self.name, errors)


class _TableValidateExistingColumnsNode(SingleChoiceDefinitionFlowNode):
    """
    We must ensure that target definition has fields
    """

    def __init__(self):
        super().__init__('table-validate-existing-columns-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        if len(target.model_fields.keys()) <= 0:
            raise NodeException(self.name, [f'Class {target} must define columns.'])


class _TableValidateMutuallyExclusiveMetadataNode(SingleChoiceDefinitionFlowNode):
    """
    We must ensure that target definition fields has no two metadata instances indicated by mutually_exclusive pairs at the same time.
    """

    def __init__(self):
        super().__init__('table-validate-mutually-exclusive-metadata-node')
        self.mutually_exclusive: list[tuple[type, type]] = [
            (meta.default_value, meta.default_nextval)]

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for field, info in target.model_fields.items():
            for tp1, tp2 in self.mutually_exclusive:
                tp1inst: Optional[Any] = extract_first_instance_from_field_metadata(info, tp1)
                tp2inst: Optional[Any] = extract_first_instance_from_field_metadata(info, tp2)
                if tp1inst is not None and tp2inst is not None:
                    errors.append(f'Field {field} described by two mutually exclusive metadata instances: {repr(tp2inst)} and {repr(tp1inst)}')
        if len(errors) > 0:
            raise NodeException(self.name, errors)


class _TableValidateSameTypeMetaInstancesHaveDifferentNamesNode(ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode):
    def __init__(self):
        super().__init__('table-validate-same-type-meta-instances-have-different-names-node',
                         types=[meta.check])


class _TableValidateRestrictedMetadataTypesNode(CommonValidateRestrictedMetadataTypesNode):
    def __init__(self):
        super().__init__('table-validate-restricted-metadata-types-node',
                         types=[meta.check, meta.default_value, meta.default_nextval, meta.comment])


class _TableValidateUniqueMetadataTypesNode(ModelValidateUniqueMetadataTypesNode):
    def __init__(self):
        super().__init__('table-validate-unique-metadata-types-node',
                         types=[meta.default_value, meta.default_nextval, meta.comment])


class _TableValidateFieldsBaseTypeNode(CommonValidateFieldsBaseTypeNode):
    def __init__(self):
        super().__init__('table-validate-fields-base-type-node',
                         type_subclass=[enums, builtin, composite],
                         type_instance=[builtin])


class _TableDependsOnValidationNodes:
    def get_dependencies(self) -> tuple[str]:
        return ('table-validate-consistent-base-classes-node',
                'table-validate-mutually-exclusive-metadata-node',
                'table-validate-restricted-metadata-types-node',
                'table-validate-unique-metadata-types-node',
                'table-validate-same-type-meta-instances-have-different-names-node',
                'table-validate-fields-base-type-node',
                'table-merge-inherited-fields-node',
                'table-validate-existing-columns-node')


class _TableExtractCheckConstraintsNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('table-extract-check-constraints-node')
        self._context = OperandDefinitionContext.TABLE

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        checks: dict[str, meta.check] = {}
        for field, ck in extract_by_instance_type_from_model_fields_info(target, meta.check):
            ck.predicate.propagate_definition(target.model_fields[field].annotation, field, self._context)
            ck.name = f'{target.__name__}_{ck.name}'
            if ck.name not in checks:
                checks[ck.name] = ck
            else:
                checks[ck.name].predicate = checks[ck.name].predicate & ck.predicate
        accumulator.add_definition('check_constraints', checks if checks != {} else None)


class _TableExtractColumnsNode(SingleChoiceDefinitionFlowNode, _TableDependsOnValidationNodes):
    def __init__(self):
        super().__init__('table-extract-column-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de columna
        columns: dict[str, dict[str, Any]] = {}
        for name, info in extract_definition_fields(target):
            col_data: dict[str, Any] = {
                'name': name,
                'type': info.annotation}
            comment_inst: Optional[meta.comment] = extract_first_instance_from_field_metadata(info, meta.comment)
            col_data['comment'] = comment_inst
            default: Optional[meta.default_value | meta.default_nextval] = extract_first_instance_from_field_metadata(info, meta.default_value)
            if default is not None:
                default.default.propagate_definition(target.model_fields[name].annotation, name, OperandDefinitionContext.TABLE)
            else:
                default = extract_first_instance_from_field_metadata(info, meta.default_nextval)
            col_data['default_value'] = default
            columns[name] = col_data
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
        definition['base_classes'] = tuple(target.__bases__) if len(target.__bases__) > 1 else None
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


table_flow_builder\
    .at_work_path('validation')\
        .add_node(_TableValidateConsistentBaseClassesNode)\
        .add_node(_TableValidateExistingColumnsNode)\
        .add_node(_TableValidateMutuallyExclusiveMetadataNode)\
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
        definition = getattr(target, '__pg_definition')()
        invalid_columns: set[str] = set(self.primary_key['columns']) - set(target.model_fields.keys())
        assert definition['primary_key'] is None
        if len(invalid_columns) > 0:
            raise TypeError(f'Invalid primary key definition, columns "{invalid_columns}" not present in table definition')
        definition['primary_key'] = self.primary_key
        return target


class foreign_key:
    def __init__(
        self, *, name: str,  columns: tuple[str, ...], other_class: type[table],
        other_class_columns: tuple[str, ...],
        on_update: foreign_key_action = foreign_key_action.NO_ACTION,
        on_delete: foreign_key_action = foreign_key_action.NO_ACTION
    ) -> None:
        assert len(columns) == len(other_class_columns)
        assert len(columns) > 0
        assert issubclass(other_class, table)
        self.foreign_key: dict[str, Any] = {
            'name': name,
            'columns': columns,
            'other_class': other_class,
            'other_class_columns': other_class_columns,
            'on_update': on_update,
            'on_delete': on_delete}

    def _extract_other_class_constraints(
        self, constraint_names: tuple[str, ...]
    ) -> list[dict[str, Any]]:
        other_class_pg_def: Optional[dict[str, Any]] = getattr(self.foreign_key['other_class'], '__pg_definition')()
        res: dict[str, Any] = {}
        for name in constraint_names:
            if other_class_pg_def[name] is not None:
                if 'name' in other_class_pg_def[name]:
                    res[other_class_pg_def[name]['name']] = other_class_pg_def[name]
                else:
                    res |= other_class_pg_def[name]
        return res

    def _check_for_other_class_constraints(
        self, *constraint_names: tuple[str, ...]
    ) -> list[str]:
        fk: dict[str, Any] = self.foreign_key
        constraints: list[dict[str, Any]] = self._extract_other_class_constraints(constraint_names)
        other_class_columns= set(fk['other_class_columns'])
        if len(constraints) == 0 or not any([len(other_class_columns - set(const['columns'])) == 0 for _, const in constraints.items()]):
            raise TypeError(f'Foreign key "{fk["name"]}" error: Other class "{fk["other_class"]}" must define any {constraint_names} constraint over referenced columns {fk["other_class_columns"]}')

    def _check_other_class_column_types(
        self, target: type[table]
    ) -> list[str]:
        fk: dict[str, Any] = self.foreign_key
        for ix in range(0, len(self.foreign_key['columns'])):
            column: FieldInfo = target.model_fields[fk['columns'][ix]]
            if fk['other_class_columns'][ix] not in fk['other_class'].model_fields:
                raise TypeError(f'Foreign key column "{fk["other_class_columns"][ix]}" must exist in <class \'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test2\'> definition')
            other_column: FieldInfo = fk['other_class'].model_fields[fk['other_class_columns'][ix]]
            if extract_type(column.annotation) != extract_type(other_column.annotation):
                raise TypeError(f'Foreign key column "{fk["columns"][ix]}" type must match with "{fk['other_class_columns'][ix]}" in {fk["other_class"]} definition')

    def __call__(self, target: type):
        assert issubclass(target, table)
        definition = getattr(target, '__pg_definition')()
        assert self.foreign_key['name'] not in definition['foreign_keys']
        invalid_columns: set[str] = set(self.foreign_key['columns']) - set(target.model_fields.keys())
        if len(invalid_columns) > 0:
            raise TypeError(f'Invalid foreign key definition, columns "{invalid_columns}" not present in table definition')
        self._check_other_class_column_types(target)
        self._check_for_other_class_constraints('unique_constraints', 'primary_key', 'indexes')
        definition['foreign_keys'][self.foreign_key['name']] = self.foreign_key
        return target


class unique_constraint:
    def __init__(self, name: str,  columns: tuple[str, ...]) -> None:
        assert len(columns) > 0
        self.unique_constraint: dict[str, Any] = {
            'name': name,
            'columns': columns}

    def __call__(self, target: type):
        assert issubclass(target, table)
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
        assert issubclass(target, table)
        definition = getattr(target, '__pg_definition')()
        assert self.index['name'] not in definition['indexes']
        invalid_columns: set[str] = set(self.index['columns']) - set(target.model_fields.keys())
        if len(invalid_columns) > 0:
            raise TypeError(f'Invalid index definition, columns "{invalid_columns}" not present in table definition')
        definition['indexes'][self.index['name']] = self.index
        return target
