from typing import\
    Any,\
    Optional,\
    Union,\
    Callable
from typing_extensions import\
    Self
import pgdriver as pg
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
class Alter(WrapsComponent, GeneratesSQLSentence):
    def __init__(
        self, component: Component, change: Union['Add', 'Drop', 'Rename', 'Set']
    ) -> None:
        WrapsComponent.__init__(self, component)
        self.change = change


class Rename(WrapsComponent, GeneratesSQLSentence):
    def __init__(self, component: Component, old_name: str):
        WrapsComponent.__init__(self, component)
        self.old_name = old_name


class Set(WrapsComponent, GeneratesSQLSentence):
    pass


class Add(WrapsComponent, GeneratesSQLSentence):
    pass


class Drop(WrapsComponent, GeneratesSQLSentence):
    pass


class Create(WrapsComponent, GeneratesSQLSentence):
    pass


class ChecksDefinitionPresence:
    def check_definition_is_present(self):
        if self.definition is None:
            raise TypeError(f'Error definition_value_is_present: "{self.name}" must be present in "{self.parent.name}" definition')

    def check_definition_is_not_present(self):
        if self.definition is not None:
            raise TypeError(f'Error definition_value_is_not_present: "{self.name}" must not be present in "{self.parent.name}" definition')


class Droppable(ChecksDefinitionPresence):
    def drop(self) -> Drop:
        self.check_definition_is_not_present()
        return self.__class__.Drop(self)


class Addable(ChecksDefinitionPresence):
    def add(self) -> Add:
        self.check_definition_is_present()
        return self.__class__.Add(self)


class Alterable:
    def alter(self, change: Union[Add, Drop, 'Alter', 'Rename']) -> Alter:
        return self.__class__.Alter(self, change)


class Creatable:
    def create(self) -> Create:
        return self.__class__.Create(self)


class Renamable(ChecksDefinitionPresence):
    def rename_from(self, old_name: str) -> Rename:
        self.check_definition_is_present()
        assert self.name != old_name
        return self.__class__.Rename(self, old_name)


class Settable(ChecksDefinitionPresence):
    def set(self) -> Set:
        self.check_definition_is_present()
        return self.__class__.Set(self)


class Type(Component, Settable):
    class Set(Set):
        def sql_sentence_params(self) -> GeneratesSQLSentence:
            return ('TYPE {}.{}', [sql.Identifier(self.component.definition['schema'].__name__), sql.Identifier(self.component.definition['type'].__name__)], [])


class TypeBuilder(Builder):
    def __init__(
        self, parent_builder: Builder,
        tp: Type, alter_lambda: Callable[[Builder, Set], None]
    ) -> None:
        self.parent_builder = parent_builder
        self.tp = tp
        self.alter_lambda = alter_lambda

    def set(self) -> Builder:
        self.parent_builder.append(self.alter_lambda(self.tp.parent, self.tp.set()))
        return self.parent_builder


class Comment(Component, Droppable, Addable):
    pass


class Constraint(Component, Droppable, Addable, Renamable):
    class Add(Add):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('ADD CONSTRAINT {} ', [sql.Identifier(self.component.name)], [], )

    class Drop(Drop):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('DROP CONSTRAINT {}', [sql.Identifier(self.component.name)], [], )

    class Rename(Rename):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('RENAME CONSTRAINT {} TO {}', [sql.Identifier(self.old_name), sql.Identifier(self.component.name)], [], )


class PrimaryKey(Constraint):
    class Add(Add):
        def sql_sentence_params(self) -> SQLSentenceParams:
            columns: list[str] = [sql.Identifier(col) for col in self.component.definition['columns']]
            placeholders: list[str] = ['{}']*len(columns)
            return ('ADD CONSTRAINT {} PRIMARY KEY ' + f'({", ".join(placeholders)})', [sql.Identifier(self.component.name)] + columns, [], )


class ForeignKey(Constraint):
    class Add(Add):
        def sql_sentence_params(self) -> SQLSentenceParams:
            columns: list[str] = [sql.Identifier(col) for col in self.component.definition['columns']]
            placeholders: list[str] = ['{}']*len(columns)
            return ('ADD CONSTRAINT {} FOREIGN KEY ' + f'({", ".join(placeholders)})', [sql.Identifier(self.component.name)] + columns, [], )


class UniqueConstraint(Constraint):
    class Add(Add):
        def sql_sentence_params(self) -> SQLSentenceParams:
            columns: list[str] = [sql.Identifier(col) for col in self.component.definition['columns']]
            placeholders: list[str] = ['{}']*len(columns)
            return ('ADD CONSTRAINT {} UNIQUE ' + f'({", ".join(placeholders)})', [sql.Identifier(self.component.name)] + columns, [], )


class CheckConstraint(Constraint):
    class Add(Add):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('ADD CONSTRAINT {} CHECK {}', [sql.Identifier(self.component.name), sql.SQL(str(self.component.definition))], [], )


class ConstraintBuilder(Builder):
    def __init__(
        self, parent_builder: Union['TableBuilder', 'DomainBuilder'],
        constraint: Constraint
    ) -> None:
        self.parent_builder = parent_builder
        self.constraint = constraint

    def rename_from(self, *, old_name: str) -> Union['TableBuilder', 'DomainBuilder']:
        self.parent_builder.append(self.constraint.parent.alter(self.constraint.rename_from(old_name)))
        return self.parent_builder

    def add(self) -> Union['TableBuilder', 'DomainBuilder']:
        self.parent_builder.append(self.constraint.parent.alter(self.constraint.add()))
        return self.parent_builder

    def drop(self) -> Union['TableBuilder', 'DomainBuilder']:
        self.parent_builder.append(self.constraint.parent.alter(self.constraint.drop()))
        return self.parent_builder


class Expression(Component, Droppable, Addable):
    def __init__(
        self, name: str, parent: Component, definition: Optional[Any]
    ) -> None:
        Component.__init__(self, name, definition, parent)


class Default(Component, Droppable, Settable):
    class Set(Set):
        def sql_sentence_params(self) -> SQLSentenceParams:
            if isinstance(self.component.definition, pg.meta.default_value):
                return ('SET DEFAULT {}', [sql.SQL(str(self.component.definition))], [], )
            elif isinstance(self.component.definition, pg.meta.default_nextval):
                seq_def: dict[str, Any] = getattr(self.component.definition.seq, '__pg_definition')()
                return ('SET DEFAULT nextval(%s)', [], [f'{seq_def["schema"]}.{self.component.definition.seq.__name__}'], )
            else:
                raise ValueError(f'Unkown default value type: "{self.component.definition}"')

    class Drop(Drop):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('DROP DEFAULT', [], [], )


class DefaultBuilder(Builder):
    def __init__(
        self, parent_builder: Union['TableColumnBuilder', 'DomainBuilder'],
        default: Default, alter_lambda: Callable[[Component, Union[Set, Drop]], Union['TableColumnBuilder', 'DomainBuilder']]
    ) -> None:
        self.parent_builder = parent_builder
        self.default = default
        self.alter_lambda = alter_lambda

    def set(self) -> Union['ColumnBuilder', 'DomainBuilder']:
        self.parent_builder.append(self.alter_lambda(self.default.parent, self.default.set()))
        return self.parent_builder

    def drop(self) -> Union['ColumnBuilder', 'DomainBuilder']:
        self.parent_builder.append(self.alter_lambda(self.default.parent, self.default.drop()))
        return self.parent_builder


class Column(Component, Alterable, Droppable, Addable, Renamable):
    class SetType(Alter):
        def __init__(self, component: 'Column', old_type: type, new_type: type) -> None:
            Alter.__init__(component)
            self.old_type: type = old_type
            self.new_type: type = new_type

    class Add(Add):
        def sql_sentence_params(self) -> SQLSentenceParams:
            tdef: dict[str, Any] = getattr(self.component.definition["type"], '__pg_definition')()
            return ('ADD COLUMN {} {}.{}', [sql.Identifier(self.component.name), sql.Identifier(tdef['schema'].__name__), sql.Identifier(tdef['type'].__name__)], [], )

    class Alter(Alter):
        def sql_sentence_params(self) -> SQLSentenceParams:
            change_sentence, change_identifiers, change_params = self.change.sql_sentence_params()
            return ('ALTER COLUMN {} ' + change_sentence, [sql.Identifier(self.component.name)] + change_identifiers, change_params)

    class Drop(Drop):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('DROP COLUMN {}', [sql.Identifier(self.component.name)], [], )

    class Rename(Rename):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('RENAME COLUMN {} TO {}', [sql.Identifier(self.old_name), sql.Identifier(self.component.name)], [], )


class TableColumnBuilder(Builder):
    def __init__(self, parent_builder: 'TableBuilder', column: Column):
        self.column = column
        self.parent_builder = parent_builder

    def default(self) -> DefaultBuilder:
        default = Default('default_value', self.column, self.column.definition['default_value'])
        return DefaultBuilder(
            self.parent_builder, default,
            lambda column, change: column.parent.alter(column.alter(change)))

    def type(self) -> TypeBuilder:
        tp: Type = Type('type', self.column, getattr(self.column.definition['type'], '__pg_definition')())
        return TypeBuilder(
            self.parent_builder, tp,
            lambda column, change: column.parent.alter(column.alter(change)))

    def add(self) -> 'TableBuilder':
        self.parent_builder.append(self.column.parent.alter(self.column.add()))
        return self.parent_builder

    def drop(self) -> 'TableBuilder':
        self.parent_builder.append(self.column.parent.alter(self.column.drop()))
        return self.parent_builder

    def rename_from(self, *, old_name: str) -> 'TableBuilder':
        self.parent_builder.append(self.column.parent.alter(self.column.rename_from(old_name)))
        return self.parent_builder


class Index(Component, Droppable, Renamable, Creatable, Alterable):
    class Create(Create):
        def sql_sentence_params(self) -> SQLSentenceParams:
            columns: list[str] = [sql.Identifier(c) for c in self.component.definition['columns']]
            placeholders: list[str] = ['{}']*len(columns)
            unique: bool = self.component.definition['unique']
            tp: pg.index_type = str(self.component.definition['type'].value).upper()
            schema = self.component.parent.definition['schema'].__name__
            return (f'CREATE{" UNIQUE" if unique else ""} ' + 'INDEX {} ON {}.{} USING ' + tp + f' ({", ".join(placeholders)})', [sql.Identifier(self.component.name), sql.Identifier(schema), sql.Identifier(self.component.parent.name)] + columns, [])

    class Alter(Alter):
        def sql_sentence_params(self) -> SQLSentenceParams:
            change_sentence, change_identifiers, change_params = self.change.sql_sentence_params()
            return ('ALTER INDEX {} ' + change_sentence, [sql.Identifier(self.component.name)] + change_identifiers, change_params)

    class Drop(Drop):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('DROP INDEX {}', [sql.Identifier(self.component.name)], [], )

    class Rename(Rename):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('RENAME TO {}', [sql.Identifier(self.component.name)], [], )


class IndexBuilder(list[Any], Builder):
    def __init__(self, parent_builder: 'TableBuilder', index: Index):
        list.__init__(self)
        self.index = index
        self.parent_builder = parent_builder

    def rename_from(self, *, old_name: str) -> Self:
        assert self.index.name != old_name
        t: Index = Index(old_name, self.index.parent, self.index.definition)
        self.parent_builder.append(t.alter(self.index.rename_from(old_name)))
        return self.parent_builder

    def drop(self) -> 'TableBuilder':
        self.parent_builder.append(self.index.drop())
        return self.parent_builder

    def create(self) -> 'TableBuilder':
        self.parent_builder.append(self.index.create())
        return self.parent_builder


class Table(Component, Droppable, Creatable, Alterable, Renamable):
    class Create(Create):
        def sql_sentence_params(self) -> SQLSentenceParams:
            bases: list[sql.Identifier] = []
            placeholders: list[str] = []
            base_classes: Optional[list[type]] = self.component.definition['base_classes']
            for base in [] if base_classes is None else base_classes:
                definition: dict[str, Any] = getattr(base, '__pg_definition')()
                bases += [sql.Identifier(definition['schema'].__name__), sql.Identifier(definition['type'].__name__)]
                placeholders += ['{}.{}']
            return ('CREATE TABLE {}.{} () INHERITS ' + f'({", ".join(placeholders)})' if len(bases) > 0 else 'CREATE TABLE {}.{} ()', [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)] + bases, [])

    class Alter(Alter):
        def sql_sentence_params(self) -> SQLSentenceParams:
            change_sentence, change_identifiers, change_params = self.change.sql_sentence_params()
            return ('ALTER TABLE {}.{} ' + change_sentence, [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)] + change_identifiers, change_params)

    class Drop(Drop):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('DROP TABLE {}.{}', [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)], [], )

    class Rename(Rename):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('RENAME TO {}', [sql.Identifier(self.component.name)], [], )


class TableBuilder(list[Any], Builder):
    def __init__(self, table: Table):
        list.__init__(self)
        self.table = table

    def column(self, name: str) -> TableColumnBuilder:
        c: Column = Column(name, self.table, self.table.definition['columns'].get(name, None))
        return TableColumnBuilder(self, c)

    def primary_key(self, name: str) -> ConstraintBuilder:
        constraint = PrimaryKey(name, self.table, self.table.definition['primary_key'])
        return ConstraintBuilder(self, constraint)

    def foreign_key(self, name: str) -> ConstraintBuilder:
        constraint = ForeignKey(name, self.table, self.table.definition['foreign_keys'].get(name, None))
        return ConstraintBuilder(self, constraint)

    def unique_constraint(self, name: str) -> ConstraintBuilder:
        constraint = UniqueConstraint(name, self.table, self.table.definition['unique_constraints'].get(name, None))
        return ConstraintBuilder(self, constraint)

    def check(self, name: str) -> ConstraintBuilder:
        constraint = CheckConstraint(name, self.table, self.table.definition['check'].get(name, None))
        return ConstraintBuilder(self, constraint)

    def index(self, name: str) -> ConstraintBuilder:
        constraint = Index(name, self.table, self.table.definition['indexes'].get(name, None))
        return IndexBuilder(self, constraint)

    def rename_from(self, *, old_name: str) -> Self:
        assert self.table.name != old_name
        t: Table = Table(old_name, self.table.parent, self.table.definition)
        self.append(t.alter(self.table.rename_from(old_name)))
        return self

    def create(self) -> Self:
        self.append(self.table.create())
        return self


class Attribute(Component, Renamable, Addable, Droppable, Alterable):
    class Alter(Alter):
        def sql_sentence_params(self) -> SQLSentenceParams:
            change_sentence, change_identifiers, change_params = self.change.sql_sentence_params()
            return ('ALTER ATTRIBUTE {} ' + change_sentence, [sql.Identifier(self.component.name)] + change_identifiers, change_params, )

    class Add(Add):
        def sql_sentence_params(self) -> SQLSentenceParams:
            tdef: dict[str, Any] = getattr(self.component.definition["type"], '__pg_definition')()
            return ('ADD ATTRIBUTE {} {}.{}', [sql.Identifier(self.component.name), sql.Identifier(tdef['schema'].__name__), sql.Identifier(tdef['type'].__name__)], [], )

    class Drop(Drop):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('DROP ATTRIBUTE {}', [sql.Identifier(self.component.name)], [], )

    class Rename(Rename):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('RENAME ATTRIBUTE {} TO {}', [sql.Identifier(self.old_name), sql.Identifier(self.component.name)], [], )


class CompositeAttributeBuilder(Builder):
    def __init__(self, parent_builder: 'CompositeBuilder', attribute: Attribute):
        self.attribute = attribute
        self.parent_builder = parent_builder

    def type(self) -> TypeBuilder:
        tp: Type = Type('type', self.attribute, getattr(self.attribute.definition['type'], '__pg_definition')())
        return TypeBuilder(
            self.parent_builder, tp,
            lambda attribute, change: attribute.parent.alter(attribute.alter(change)))

    def add(self) -> 'CompositeBuilder':
        self.parent_builder.append(self.attribute.parent.alter(self.attribute.add()))
        return self.parent_builder

    def rename_from(self, *, old_name: str) -> 'CompositeBuilder':
        self.parent_builder.append(self.attribute.parent.alter(self.attribute.rename_from(old_name)))
        return self.parent_builder

    def drop(self) -> 'CompositeBuilder':
        self.parent_builder.append(self.attribute.parent.alter(self.attribute.drop()))
        return self.parent_builder


class Composite(Component, Renamable, Alterable, Droppable, Creatable):
    class Create(Create):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('CREATE TYPE {}.{} AS ()', [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)], [], )

    class Alter(Alter):
        def sql_sentence_params(self) -> SQLSentenceParams:
            change_sentence, change_identifiers, change_params = self.change.sql_sentence_params()
            return ('ALTER TYPE {}.{} ' + change_sentence, [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)] + change_identifiers, change_params)

    class Rename(Rename):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('RENAME TO {}', [sql.Identifier(self.component.name)], [], )

    class Drop(Drop):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('DROP TYPE {}.{}', [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)], [], )


class CompositeBuilder(list[Any], Builder):
    def __init__(self, composite: Composite):
        list.__init__(self)
        self.composite = composite

    def attribute(self, name: str) -> CompositeAttributeBuilder:
        c: Attribute = Attribute(name, self.composite, self.composite.definition['attributes'].get(name, None))
        return CompositeAttributeBuilder(self, c)

    def rename_from(self, *, old_name: Any) -> Self:
        t: Composite = Composite(old_name, self.composite.parent, self.composite.definition)
        self.append(t.alter(self.composite.rename_from(old_name)))
        return self

    def create(self) -> Self:
        self.append(self.composite.create())
        return self

    def drop(self) -> Self:
        self.append(self.composite.drop())
        return self


class Value(Component, Addable, Renamable):
    class Add(Add):
        def sql_sentence_params(self) -> str:
            return ('ADD VALUE %s', [], [self.component.name], )

    class Rename(Rename):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('RENAME VALUE %s TO %s', [], [self.old_name, self.component.name], )


class EnumValueBuilder(Builder):
    def __init__(self, parent_builder: 'EnumBuilder', value: Value):
        self.value = value
        self.parent_builder = parent_builder

    def add(self) -> 'EnumBuilder':
        self.parent_builder.append(self.value.parent.alter(self.value.add()))
        return self.parent_builder

    def rename_from(self, *, old_name: str) -> Self:
        self.parent_builder.append(self.value.parent.alter(self.value.rename_from(old_name)))
        return self.parent_builder


class Enum(Component, Renamable, Alterable, Droppable, Creatable):
    class Create(Create):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('CREATE TYPE {}.{} AS ENUM ()', [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)], [], )

    class Alter(Alter):
        def sql_sentence_params(self) -> SQLSentenceParams:
            change_sentence, change_identifiers, change_params = self.change.sql_sentence_params()
            return ('ALTER TYPE {}.{} ' + change_sentence, [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)] + change_identifiers, change_params, )

    class Drop(Drop):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('DROP TYPE {}.{}', [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)], [], )

    class Rename(Rename):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('RENAME TO {}', [sql.Identifier(self.component.name)], [], )


class EnumBuilder(list[Any], Builder):
    def __init__(
        self, enums: Enum
    ) -> None:
        list.__init__(self)
        self.enums = enums

    def value(self, name: str) -> EnumValueBuilder:
        c: Value = Value(name, self.enums, self.enums.definition['members'].get(name, None))
        return EnumValueBuilder(self, c)

    def rename_from(self, *, old_name: str) -> Self:
        t: Enum = Enum(old_name, self.enums.parent, self.enums.definition)
        self.append(t.alter(self.enums.rename_from(old_name)))
        return self

    def create(self) -> Self:
        self.append(self.enums.create())
        return self

    def drop(self) -> Self:
        self.append(self.enums.drop())
        return self


class Domain(Component, Creatable, Alterable, Renamable, Droppable):
    class Create(Create):
        def sql_sentence_params(self) -> SQLSentenceParams:
            tdef: dict[str, Any] = getattr(self.component.definition["base_type"], '__pg_definition')()
            return ('CREATE DOMAIN {}.{} AS {}.{}', [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name), sql.Identifier(tdef['schema'].__name__), sql.Identifier(tdef['type'].__name__)], [], )

    class Alter(Alter):
        def sql_sentence_params(self) -> SQLSentenceParams:
            change_sentence, change_identifiers, change_params = self.change.sql_sentence_params()
            return ('ALTER DOMAIN {}.{} ' + change_sentence, [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)] + change_identifiers, change_params, )

    class Drop(Drop):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('DROP DOMAIN {}.{}', [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)], [], )

    class Rename(Rename):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('RENAME TO {}', [sql.Identifier(self.component.name)], [], )


class DomainBuilder(list[Any], Builder):
    def __init__(
        self, domain: Domain
    ) -> None:
        list.__init__(self)
        self.domain = domain

    def constraint(self, name: str) -> ConstraintBuilder:
        constraint = CheckConstraint(name, self.domain, self.domain.definition['check'])
        return ConstraintBuilder(self, constraint)

    def rename_from(self, *, old_name: Any) -> Self:
        t: Domain = Domain(old_name, self.composite.parent, self.domain.definition)
        self.append(t.alter(self.domain.rename_from(old_name)))
        return self

    def create(self) -> Self:
        self.append(self.domain.create())
        return self


class Sequence(Component, Creatable, Renamable, Droppable, Alterable):
    class Create(Create):
        def sql_sentence_params(self) -> SQLSentenceParams:
            base_tdef = getattr(self.component.definition["base_type"], '__pg_definition')()
            return ('CREATE SEQUENCE {}.{} AS {}.{}', [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name), sql.Identifier(base_tdef['schema'].__name__), sql.Identifier(base_tdef['type'].__name__)], [], )

    class Alter(Alter):
        def sql_sentence_params(self) -> SQLSentenceParams:
            change_sentence, change_identifiers, change_params = self.change.sql_sentence_params()
            return ('ALTER SEQUENCE {}.{} ' + change_sentence, [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)] + change_identifiers, change_params, )

    class Type(Type):
        class Set(Set):
            def sql_sentence_params(self) -> SQLSentenceParams:
                return ('AS {}.{}', [sql.Identifier(self.component.definition['schema'].__name__), sql.Identifier(self.component.definition['type'].__name__)], [])

    class MinValue(Component, Settable):
        class Set(Set):
            def sql_sentence_params(self) -> SQLSentenceParams:
                return ('MINVALUE %s', [], [self.component.definition])

    class MaxValue(Component, Settable):
        class Set(Set):
            def sql_sentence_params(self) -> SQLSentenceParams:
                return ('MAXVALUE %s', [], [self.component.definition])

    class Increment(Component, Settable):
        class Set(Set):
            def sql_sentence_params(self) -> SQLSentenceParams:
                return ('INCREMENT BY %s', [], [self.component.definition])

    class Cycle(Component, Settable):
        class Set(Set):
            def sql_sentence_params(self) -> SQLSentenceParams:
                return ('CYCLE', [], [], )

    class Rename(Rename):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('RENAME TO {}', [sql.Identifier(self.component.name)], [], )

    class Drop(Drop):
        def sql_sentence_params(self) -> SQLSentenceParams:
            return ('DROP SEQUENCE {}.{}', [sql.Identifier(self.component.parent.name), sql.Identifier(self.component.name)], [], )


class SequenceAttributeBuilder(Builder):
    def __init__(
        self, parent_builder: 'SequenceBuilder', sequence_attribute: Any
    ) -> None:
        self.sequence_attribute = sequence_attribute
        self.parent_builder = parent_builder

    def set(self) -> Builder:
        self.parent_builder.append(self.sequence_attribute.parent.alter(self.sequence_attribute.set()))
        return self.parent_builder


class SequenceBuilder(list[Any], Builder):
    def __init__(
        self, sequence: Sequence
    ) -> None:
        list.__init__(self)
        self.sequence = sequence

    def type(self) -> TypeBuilder:
        tp: Sequence.Type = Sequence.Type('type', self.sequence, getattr(self.sequence.definition['base_type'], '__pg_definition')())
        return TypeBuilder(
            self, tp, lambda sequence, change: sequence.alter(change))

    def attribute(self, name) -> SequenceAttributeBuilder:
        attr: Optional[Any] = None
        if name == 'min_value':
            attr = Sequence.MinValue(
                'min_value', self.sequence, self.sequence.definition['min_value'])
        elif name == 'max_value':
            attr = Sequence.MaxValue(
                'max_value', self.sequence, self.sequence.definition['max_value'])
        elif name == 'increment':
            attr = Sequence.Increment(
                'increment', self.sequence, self.sequence.definition['increment'])
        elif name == 'cycle':
            attr = Sequence.Cycle(
                'cycle', self.sequence, self.sequence.definition['cycle'])
        else:
            raise AttributeError(f'Invalid sequence attribute: {name}')
        return SequenceAttributeBuilder(self, attr)

    def rename_from(self, *, old_name: Any) -> Self:
        t: Sequence = Sequence(old_name, self.sequence.parent, self.sequence.definition)
        self.append(t.alter(self.sequence.rename_from(old_name)))
        return self

    def create(self) -> Self:
        self.append(self.sequence.create())
        return self

    def drop(self) -> Self:
        self.append(self.sequence.drop())
        return self


class Schema(Component):
    pass


class SchemaBuilder(list[Any], Builder):
    def __init__(
        self, schema: Schema
    ) -> None:
        list.__init__(self)
        self.schema = schema

    def _search_object(self, name: str) -> Optional[type]:
        return self.schema.definition['objects'].get(name, None)

    def _get_builder(
        self, name: str, builder_cls: type, cls: type
    ) -> Builder:
        tp: Optional[type] = self._search_object(name)
        if tp is None:
            return builder_cls(cls(name, self.schema, None))
        else:
            return builder_cls(cls(name, self.schema, getattr(tp, '__pg_definition')()))

    def table(self, name: str) -> Self:
        return self._get_builder(name, TableBuilder, Table)

    def sequence(self, name: str) -> Self:
        return self._get_builder(name, SequenceBuilder, Sequence)

    def enum(self, name: str) -> Self:
        return self._get_builder(name, EnumBuilder, Enum)

    def composite(self, name: str) -> Self:
        return self._get_builder(name, CompositeBuilder, Composite)

    def domain(self, name: str) -> Self:
        return self._get_builder(name, DomainBuilder, Domain)


def builder(schema: type) -> Builder:
    schema: Schema = Schema(schema.__name__, None, getattr(schema, '__pg_definition')())
    return SchemaBuilder(schema)
