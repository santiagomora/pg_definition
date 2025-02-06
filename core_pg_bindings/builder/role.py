from typing import\
    Any,\
    Optional,\
    Union,\
    Generator
from typing_extensions import\
    Self
from psycopg import\
    sql
from .common import\
    Component,\
    Builder,\
    WrapsComponent,\
    SQLSentenceParams,\
    GeneratesSQLSentence


__all__ = ['builder']


# TODO: add create function builder
# TODO: it must be possible to grant/revoke from roles on tables, sequences and functions
# TODO: when creating a table or a sequence it must be possible to revoke all permissions from it from all roles
# TODO: when creating a table or a sequence it must be possible to revoke all permissions from it
# TODO: add create role builder for permissions as groups of grants over defined objects, and roles as groups of permissions
class HandlesPlaceholders:
    def get_placeholders(self) -> tuple[str, list[sql.Identifier], str]:
        placeholder: str = ''
        identifiers: list[sql.Identifier] = []
        if self.component.parent is not None:
            placeholder = '{}.{}'
            identifiers = [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)]
        else:
            placeholder = '{}'
            identifiers = [sql.Identifier(self.component.name)]
        return placeholder, identifiers, self.component.definition['kind'].upper()


class Grant(WrapsComponent, GeneratesSQLSentence, HandlesPlaceholders):
    def __init__(
        self, over: Component, action: Component
    ) -> None:
        WrapsComponent.__init__(self, over)
        self.permission = action.parent
        self.action = action


class Revoke(WrapsComponent, GeneratesSQLSentence, HandlesPlaceholders):
    def __init__(
        self, over: Component, action: Component
    ) -> None:
        WrapsComponent.__init__(self, over)
        self.action = action
        self.permission = action.parent


class ChecksDefinitionPresence:
    def check_definition_is_present(self, over: Component):
        if self.definition is None:
            raise TypeError(f'Error definition_value_is_present: "{self.name}" must be present in "{self.parent.name}" definition grants over "{over.name}"')

    def check_definition_is_not_present(self, over: Component):
        if self.definition is not None:
            raise TypeError(f'Error definition_value_is_not_present: "{self.name}" must not be present in "{self.parent.name}" definition grants over "{over.name}"')


class Grantable(ChecksDefinitionPresence):
    class Grant(Grant):
        pass

    def grant(self, over: Component) -> Grant:
        self.check_definition_is_present(over)
        return self.__class__.Grant(over, self)


class Revokable(ChecksDefinitionPresence):
    class Revoke(Revoke):
        pass

    def revoke(self, over: Component) -> Grant:
        self.check_definition_is_not_present(over)
        return self.__class__.Revoke(over, self)


class Select(Component, Grantable, Revokable):
    class Grant(Grant):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'GRANT SELECT ON {kind} {placeholder} TO ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Select.Revoke\
                and self.component.definition['type'] != other.component.definition['type']

    class Revoke(Revoke):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'REVOKE SELECT ON {kind} {placeholder} FROM ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Select.Grant\
                and self.component.definition['type'] != other.component.definition['type']


class Insert(Component, Grantable, Revokable):
    class Grant(Grant):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'GRANT INSERT ON {kind} {placeholder} TO ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Insert.Revoke\
                and self.component.definition['type'] != other.component.definition['type']

    class Revoke(Revoke):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'REVOKE INSERT ON {kind} {placeholder} FROM ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Insert.Grant\
                and self.component.definition['type'] != other.component.definition['type']


class Update(Component, Grantable, Revokable):
    class Grant(Grant):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'GRANT UPDATE ON {kind} {placeholder} TO ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Update.Revoke\
                and self.component.definition['type'] != other.component.definition['type']

    class Revoke(Revoke):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'REVOKE UPDATE ON {kind} {placeholder} FROM ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Update.Grant\
                and self.component.definition['type'] != other.component.definition['type']


class Delete(Component, Grantable, Revokable):
    class Grant(Grant):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'GRANT DELETE ON {kind} {placeholder} TO ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Delete.Revoke\
                and self.component.definition['type'] != other.component.definition['type']

    class Revoke(Revoke):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'REVOKE DELETE ON {kind} {placeholder} FROM ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Delete.Grant\
                and self.component.definition['type'] != other.component.definition['type']


class Truncate(Component, Grantable, Revokable):
    class Grant(Grant):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers = self.get_placeholders()
            return (f'GRANT TRUNCATE ON {placeholder} TO ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Truncate.Revoke\
                and self.component.definition['type'] != other.component.definition['type']

    class Revoke(Revoke):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'REVOKE TRUNCATE ON {kind} {placeholder} FROM ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Truncate.Grant\
                and self.component.definition['type'] != other.component.definition['type']


class Usage(Component, Grantable, Revokable):
    class Grant(Grant):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'GRANT USAGE ON {kind} {placeholder} TO ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Usage.Revoke\
                and self.component.definition['type'] != other.component.definition['type']

    class Revoke(Revoke):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'REVOKE USAGE ON {kind} {placeholder} FROM ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Usage.Grant\
                and self.component.definition['type'] != other.component.definition['type']


class Execute(Component, Grantable, Revokable):
    class Grant(Grant):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'GRANT EXECUTE ON {kind} {placeholder} TO ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Execute.Revoke\
                and self.component.definition['type'] != other.component.definition['type']

    class Revoke(Revoke):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'REVOKE EXECUTE ON {kind} {placeholder} FROM ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Execute.Grant\
                and self.component.definition['type'] != other.component.definition['type']


class Create(Component, Grantable, Revokable):
    class Grant(Grant):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'REVOKE CREATE ON {kind} {placeholder} TO ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Create.Revoke\
                and self.component.definition['type'] != other.component.definition['type']

    class Revoke(Revoke):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            return (f'REVOKE CREATE ON {kind} {placeholder} FROM ' + '{}', identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Create.Grant\
                and self.component.definition['type'] != other.component.definition['type']


class Role(Component, Grantable, Revokable):
    class Grant(Grant):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('GRANT {} TO {}', [sql.Identifier(self.action.name), sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Role.Revoke\
                and self.component.definition['type'] != other.component.definition['type']

    class Revoke(Revoke):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('REVOKE {} FROM {}', [sql.Identifier(self.action.name), sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == Role.Grant\
                and self.component.definition['type'] != other.component.definition['type']


class References(Component, Grantable, Revokable):
    class Grant(Grant):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            columns_ph: list[str] = ['{}']*len(self.action.columns)
            return (f'GRANT REFERENCES ({", ".join(columns_ph)}) ON {placeholder} TO ' + '{}', [sql.Identifier(col) for col in self.action.columns] + identifiers +  [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == References.Revoke\
                and self.component.definition['type'] != other.component.definition['type']

    class Revoke(Revoke):
        def sql_sentence_params(self) -> SQLSentenceParams:
            placeholder, identifiers, kind = self.get_placeholders()
            columns_ph: list[str] = ['{}']*len(self.action.columns)
            return (f'REVOKE REFERENCES ({", ".join(columns_ph)}) ON {placeholder} FROM ' + '{}', [sql.Identifier(col) for col in self.action.columns] + identifiers + [sql.Identifier(self.permission.name)], [], )

        def is_opposite(self, other: GeneratesSQLSentence) -> bool:
            return other.__class__ == References.Grant\
                and self.component.definition['type'] != other.component.definition['type']

    def __init__(
        self, name: str, columns: tuple[str, ...], parent: Optional['Component'] = None,
        definition: Optional[dict[str, Any]] = None
    ) -> None:
        Component.__init__(self, name, parent, definition)
        self.columns = columns



class PermissionActionBuilder(Builder):
    def __init__(
        self, parent_builder: Builder, over: Component,
        action: Union[Grantable, Revokable]
    ) -> None:
        self.parent_builder = parent_builder
        self.action = action
        self.over = over

    def grant(self) -> Builder:
        self.parent_builder.append(self.action.grant(self.over))
        return self.parent_builder

    def revoke(self) -> Builder:
        self.parent_builder.append(self.action.revoke(self.over))
        return self.parent_builder


class Table(Component):
    pass


class TableBuilder(Builder):
    def __init__(
        self, parent_builder: 'PermissionBuilder', permission: 'Permission',
        table: Table
    ) -> None:
        self.parent_builder = parent_builder
        self.table = table
        self.permission = permission

    def select(self) -> PermissionActionBuilder:
        return PermissionActionBuilder(
            self.parent_builder, self.table,
            Select('select', self.permission, self.permission.get_grant(self.table.definition['type'], 'select'))
        )

    def insert(self) -> PermissionActionBuilder:
        return PermissionActionBuilder(
            self.parent_builder, self.table,
            Insert('insert', self.permission, self.permission.get_grant(self.table.definition['type'], 'insert'))
        )

    def update(self) -> PermissionActionBuilder:
        return PermissionActionBuilder(
            self.parent_builder, self.table,
            Update('update', self.permission,  self.permission.get_grant(self.table.definition['type'], 'update'))
        )

    def delete(self) -> PermissionActionBuilder:
        return PermissionActionBuilder(
            self.parent_builder, self.table,
            Delete('delete', self.permission, self.permission.get_grant(self.table.definition['type'], 'delete'))
        )

    def truncate(self) -> PermissionActionBuilder:
        return PermissionActionBuilder(
            self.parent_builder, self.table,
            Truncate('truncate', self.permission, self.permission.get_grant(self.table.definition['type']))
        )

    def references(self) -> PermissionActionBuilder:
        columns: tuple[str, ...] = self.permission.get_grant(self.table.definition['type'], 'references')
        return PermissionActionBuilder(
            self.parent_builder, self.table,
            References('references', columns, self.permission, columns)
        )


class Function(Component):
    pass


class FunctionBuilder(Builder):
    def __init__(
        self, parent_builder: 'PermissionBuilder', permission: 'Permission', function: Function
    ) -> None:
        self.parent_builder = parent_builder
        self.function = function
        self.permission = permission

    def execute(self) -> PermissionActionBuilder:
        return PermissionActionBuilder(
            self.parent_builder, self.function,
            Execute('execute', self.permission, self.permission.get_grant(self.function.definition['type'], 'execute'))
        )


class Sequence(Component):
    pass


class SequenceBuilder(Builder):
    def __init__(
        self, parent_builder: 'PermissionBuilder', permission: 'Permission', sequence: Sequence
    ) -> None:
        self.parent_builder = parent_builder
        self.sequence = sequence
        self.permission = permission

    def select(self) -> PermissionActionBuilder:
        return PermissionActionBuilder(
            self.parent_builder, self.sequence,
            Select('select', self.permission, self.permission.get_grant(self.sequence.definition['type'], 'select')))

    def update(self) -> PermissionActionBuilder:
        return PermissionActionBuilder(
            self.parent_builder, self.sequence, 
            Update('update', self.permission, self.permission.get_grant(self.sequence.definition['type'], 'update'))
        )

    def usage(self) -> PermissionActionBuilder:
        return PermissionActionBuilder(
            self.parent_builder, self.sequence,
            Usage('usage', self.permission, self.permission.get_grant(self.sequence.definition['type'], 'usage'))
        )


class Schema(Component):
    pass


class SchemaBuilder(Builder):
    def __init__(
        self, parent_builder: 'PermissionBuilder', permission: 'Permission', schema: Schema
    ) -> None:
        self.parent_builder = parent_builder
        self.schema = schema
        self.permission = permission

    def usage(self) -> PermissionActionBuilder:
        return PermissionActionBuilder(
            self.parent_builder, self.schema,
            Usage('usage', self.permission, self.permission.get_grant(self.schema.definition['type'], 'usage'))
        )

    def create(self) -> PermissionActionBuilder:
        return PermissionActionBuilder(
            self.parent_builder, self.schema,
            Create('create', self.permission, self.permission.get_grant(self.schema.definition['type'], 'create'))
        )


class Permission(Component):
    class Create(WrapsComponent):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('CREATE ROLE {}', [sql.Identifier(self.component.name)], [], )

    class Drop(WrapsComponent):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('DROP ROLE {}', [sql.Identifier(self.component.name)], [], )

    def get_grant(self, tp: type, name: str) -> Any:
        has_perm: Any = self.definition.get('type_grants', {}).get(tp, {}).get('grants', {}).get(name, None)
        return has_perm


class PermissionBuilder(list[Any], Builder):
    def __init__(
        self, permission: Permission
    ) -> None:
        list.__init__(self)
        self.permission = permission

    def table(self, table: type) -> 'TableBuilder':
        definition: dict[str, Any] = table._postgres_definition
        parent: Schema = Schema(definition['schema'].__name__, None, definition['schema']._postgres_definition)
        return TableBuilder(
            self, self.permission, Table(table.__name__, parent, definition)
        )

    def sequence(self, sequence: type) -> 'SequenceBuilder':
        definition: dict[str, Any] = sequence._postgres_definition
        parent: Schema = Schema(definition['schema'].__name__, None, definition['schema']._postgres_definition)
        return SequenceBuilder(
            self, self.permission, Sequence(sequence.__name__, parent, definition)
        )

    def function(self, function: type) -> 'FunctionBuilder':
        definition: dict[str, Any] = function._postgres_definition
        parent: Schema = Schema(definition['schema'].__name__, None, definition['schema']._postgres_definition)
        return FunctionBuilder(
            self, self.permission, Function(function.__name__, parent, definition)
        )

    def schema(self, schema: type) -> 'SchemaBuilder':
        definition: dict[str, Any] = schema._postgres_definition
        return SchemaBuilder(
            self, self.permission, Schema(schema.__name__, None, definition)
        )

    def role(self, role: type) -> 'PermissionActionBuilder':
        return PermissionActionBuilder(
            self, self.permission,
            Role(role.__name__, self.permission, None if role not in self.permission.definition['permissions'] else True)
        )

    def create(self) -> Self:
        self.append(Permission.Create(self.permission))
        return self

    def drop(self) -> Self:
        self.append(Permission.Drop(self.permission))
        return self


class RoleBuilder(list[Any], Builder):
    def __init__(
        self, role: Permission
    ) -> None:
        list.__init__(self)
        self.role = role

    def permission(self, permission: type) -> 'PermissionActionBuilder':
        return PermissionActionBuilder(
            self, self.role,
            Role(permission.__name__, self.role, None if permission not in self.role.definition['permissions'] else True)
        )

    def create(self) -> Self:
        self.append(Permission.Create(self.role))
        return self

    def drop(self) -> Self:
        self.append(Permission.Drop(self.role))
        return self


def builder(permission: type) -> Builder:
    perm: Permission = Permission(permission.__name__, None, permission._postgres_definition)
    return RoleBuilder(perm) if perm.definition['kind'] == 'role' else PermissionBuilder(perm)
