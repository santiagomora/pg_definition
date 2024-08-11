from abc import\
    ABC,\
    abstractmethod
from dataclasses import\
    dataclass
from typing import\
    Any,\
    Type,\
    Generic,\
    get_args,\
    Protocol,\
    TypeVar,\
    Union,\
    cast,\
    Optional,\
    Callable,\
    Sized
from pydantic_core import\
    core_schema
from pydantic import\
    GetCoreSchemaHandler,\
    ValidationInfo
from pydantic.fields import\
    FieldInfo
from pydantic import\
    BaseModel
from datetime import\
    datetime,\
    time,\
    date
from pgdriver.definition.inspection import\
    extract_by_instance_type_from_inherited_classes,\
    is_optional,\
    extract_type
from numbers import\
    Number
from typing_extensions import\
    Self
from pgdriver.definition.build import\
    pg_table,\
    pg_bigint,\
    pg_int,\
    pg_decimal,\
    pg_double,\
    pg_time,\
    pg_timetz,\
    pg_date,\
    pg_past_date,\
    pg_future_date,\
    pg_text,\
    pg_timestamp,\
    pg_past_timestamp,\
    pg_future_timestamp,\
    pg_timestamptz,\
    pg_past_timetstampz,\
    pg_bool,\
    pg_composite,\
    pg_json,\
    pg_future_timestamptz,\
    pg_sequence
from pgdriver.definition.extraction.base import\
    pg_table_index_type,\
    pg_table_foreign_key_action


type_compatibility: dict[type, type] = {
    pg_bigint: Number,
    pg_int: Number,
    pg_decimal: Number,
    pg_double: Number,
    pg_time: time,
    pg_timetz: time,
    pg_date: date,
    pg_past_date: date,
    pg_future_date: date,
    pg_text: str,
    pg_timestamp: datetime,
    pg_past_timestamp: datetime,
    pg_future_timestamp: datetime,
    pg_timestamptz: datetime,
    pg_past_timetstampz: datetime,
    pg_bool: bool,
    pg_composite: pg_composite,
    pg_json: str,
    pg_future_timestamptz: datetime}


class SupportLen(Protocol):
    def __len__(self) -> int: ...


class SupportLe(Protocol):
    def __le__(self, other: Any) -> bool: ...


class SupportLt(Protocol):
    def __lt__(self, other: Any) -> bool: ...


class SupportGe(Protocol):
    def __ge__(self, other: Any) -> bool: ...


class SupportGt(Protocol):
    def __gt__(self, other: Any) -> bool: ...


class SupportEq(Protocol):
    def __eq__(self, other: Any) -> bool: ...


class SupportNe(Protocol):
    def __ne__(self, other: Any) -> bool: ...


class SupportAdd(Protocol):
    def __add__(self, other: Any) -> Any: ...
    def __radd__(self, other: Any) -> Any: ...


class SupportSub(Protocol):
    def __sub__(self, other: Any) -> Any: ...
    def __rsub__(self, other: Any) -> Any: ...


class SupportTDiv(Protocol):
    def __truediv__(self, other: Any) -> Any: ...
    def __rtruediv__(self, other: Any) -> Any: ...


class SupportMod(Protocol):
    def __mod__(self, other: Any) -> Any: ...
    def __rmod__(self, other: Any) -> Any: ...


class SupportMul(Protocol):
    def __mul__(self, other: Any) -> Any: ...
    def __rmul__(self, other: Any) -> Any: ...


T = TypeVar('T', bound=Union[
    Sized,
    SupportLe,
    SupportLt,
    SupportGe,
    SupportGt,
    SupportEq,
    SupportNe,
    SupportAdd,
    SupportSub,
    SupportTDiv,
    SupportMod,
    SupportMul
])

V = TypeVar('V')

SLE = TypeVar('SLE', bound=SupportLe)
SLT = TypeVar('SLT', bound=SupportLt)
SGE = TypeVar('SGE', bound=SupportGe)
SGT = TypeVar('SGT', bound=SupportGt)
SEQ = TypeVar('SEQ', bound=SupportEq)
SNE = TypeVar('SNE', bound=SupportNe)
SADD = TypeVar('SADD', bound=SupportAdd)
SSUB = TypeVar('SSUB', bound=SupportSub)
STDIV = TypeVar('STDIV', bound=SupportTDiv)
SMOD = TypeVar('SMOD', bound=SupportMod)
SMUL = TypeVar('SMUL', bound=SupportMul)


class Reference(BaseModel, Generic[T]):
    def __init__(self) -> None:
        BaseModel.__init__(self)

    # por definir lo que devuelve
    @abstractmethod
    def as_str(self, column_name: str) -> dict[str, Any]:
        pass

    @abstractmethod
    def value(self, info: dict[str, Any]) -> T:
        pass


class FieldRef(Reference[T]):
    def __init__(self, field_name: str) -> None:
        super().__init__()
        # el field debe ser un atributo de la clase que registra la anotacion
        self._field_name: str = field_name

    # def to_description_dict(self, column_name: str) -> dict[str, Any]:
        # return {'left_operand': column_name,
                # 'right_operand': self._field_name}

    def value(self, info: dict[str, Any]) -> T:
        # info tiene un atributo data con los datos validos del modelo
        # para poder validar la dependencia entre dos campos
        # es necesario que el campo que define la relacion aparezca
        # despues del objetivo en la definicion del modelo
        return cast(T, info[self._field_name])

    # no se si column_name sea apropiado para los Ref
    def as_str(self, column_name: str) -> str:
        return self._field_name


class LiteralRef(Reference[T]):
    def __init__(self, literal: T) -> None:
        super().__init__()
        self._literal = literal

    # no se si column_name sea apropiado para los Ref
    def as_str(self, column_name: str) -> str:
        return str(self._literal)

    def value(self, info: dict[str, Any]) -> T:
        return self._literal


class Attribute(Generic[T, V], ABC):
    def __init__(self, wrapped_callable: Callable[[T], V]) -> None:
        self._wrapped_callable = wrapped_callable

    @abstractmethod
    def as_str(self, column_name: str) -> str:
        pass

    def call(self, ref: Reference[T], info: dict[str, Any]) -> V:
        return self._wrapped_callable(self._wrapped_callable(ref.value(info)))


class Length(Attribute[Sized, int]):
    def __init__(self) -> None:
        super().__init__(len)

    def as_str(self, column_name: str) -> str:
        return f'length({column_name})'


class AttributeRef(Reference[T], Generic[T, V]):
    # se llama atributo porque postgres permite la extraccion de atributos
    # de composites mediante notacion funcional, esto apunta a algo similar
    # attribute mas alla de ser un callable, debe ser un callable representable
    # en string
    def __init__(self, attr: Attribute[T, V], ref: Reference[V]) -> None:
        super().__init__()
        self._ref = ref
        self._attr = attr

    # esto es un attribute que se extrae con notacion funcional desde postgres
    # el attribute tiene que tener una representacion en funcional
    # el ref tiene que tener una representacion funcional
    # hay que aplicar el atributo tanto a la izquierda como a la derecha
    def as_str(self, column_name: str) -> str:
        operand: str = self._ref.as_str(column_name)
        return self._attr.as_str(operand)

    def value(self, info: dict[str, Any]) -> T:
        return self._attr.call(self._ref, info)


class OperationRef(Reference[T]):
    def __init__(self, *operands: Reference[T]) -> None:
        super().__init__()
        if len(operands) < 2:
            raise ValueError
        self._operands: tuple[Reference[T], ...] = operands

    @abstractmethod
    def operate(self, acc: T, other: T) -> T:
        pass

    def value(self, info: dict[str, Any]) -> T:
        acc: Optional[T] = None
        for op in self._operands:
            opval: T = op.value(info)
            acc = opval if acc is None else self.operate(acc, opval)
        return cast(T, acc)


class add_(OperationRef[SADD]):
    def __init__(self, *operands: Reference[SADD]) -> None:
        super().__init__(*operands)

    def operate(self, acc: SADD, other: SADD) -> SADD:
        return cast(SADD, acc + other)

    def as_str(self, column_name: str) -> str:
        operation: str = ' + '.join([operand.as_str(column_name) for operand in self._operands])
        return f'({operation})'


class sub_(OperationRef[SSUB]):
    def __init__(self, *operands: Reference[SSUB]) -> None:
        super().__init__(*operands)

    def operate(self, acc: SSUB, other: SSUB) -> SSUB:
        return cast(SSUB, acc - other)

    def as_str(self, column_name: str) -> str:
        operation: str = ' - '.join([operand.as_str(column_name) for operand in self._operands])
        return f'({operation})'


class mul_(OperationRef[SMUL]):
    def __init__(self, *operands: Reference[SMUL]):
        super().__init__(*operands)

    def operate(self, acc: SMUL, other: SMUL) -> SMUL:
        return cast(SMUL, acc * other)

    def as_str(self, column_name: str) -> str:
        operation: str = ' * '.join([operand.as_str(column_name) for operand in self._operands])
        return f'({operation})'


class div_(OperationRef[STDIV]):
    def __init__(self, *operands: Reference[STDIV]) -> None:
        super().__init__(*operands)

    def operate(self, acc: STDIV, other: STDIV) -> STDIV:
        return cast(STDIV, acc / other)

    def as_str(self, column_name: str) -> str:
        operation: str = ' / '.join([operand.as_str(column_name) for operand in self._operands])
        return f'({operation})'


class mod_(OperationRef[SMOD]):
    def __init__(self, *operands: Reference[SMOD]) -> None:
        super().__init__(*operands)

    def operate(self, acc: SMOD, other: SMOD) -> SMOD:
        return cast(SMOD, acc % other)

    def as_str(self, column_name: str) -> str:
        operation: str = ' % '.join([operand.as_str(column_name) for operand in self._operands])
        return f'({operation})'


class Specification(BaseModel, Generic[T]):
    # def _extract_underlying_type(self, annotation: type) -> set[type]:
    #     under: set[type] = set()
    #     if get_origin(annotation) == Union:
    #         for t in get_args(annotation):
    #             under = under.union(self._extract_underlying_type(t))
    #     elif get_origin(annotation) == Annotated:
    #         under = set((get_args(annotation)[0],))
    #     else:
    #         under = set((annotation, ))
    #     return under

    def check_type(self, annotated_type: type, check_type: type) -> None:
        if check_type == annotated_type:
            return
        errors: list[str] = []
        if isinstance(annotated_type, pg_domain):
            check_type = check_type.__bases__[0]
        if not isinstance(annotated_type, pg_builtin):
            errors.append('Check type must be a pg_builtin instance.')
        if annotated_type not in type_compatibility:
            errors.append(f'Compatibility not configured for type {annotated_type!r}')
        if check_type not in type_compatibility:
            errors.append(f'Compatibility not configured for type {annotated_type!r}')
        if len(errors) > 0:
            raise TypeError('Several errors detected on pg_meta.check definition: ' + ', '.join(errors))
        annotated_compat: type = type_compatibility[annotated_type]
        check_compat: type = type_compatibility[check_type]
        return issubclass(annotated_compat, check_compat) or issubclass(check_compat, annotated_compat)

    @abstractmethod
    def as_str(self, column_name: str) -> str:
        pass

    @abstractmethod
    def check_value(self, value: Any, info: dict[str, Any]) -> None:
        # valida que el valor value cumpla con el spec
        pass


class and_(Specification[T]):
    def __init__(self, *specs: Specification[T]) -> None:
        super().__init__()
        if len(specs) < 2:
            raise ValueError
        self._specs: tuple[Specification[T], ...] = specs

    def check_value(self, value: T, info: dict[str, Any]) -> None:
        errors: list[str] = []
        for spec in self._specs:
            try:
                spec.check_value(value, info)
            except ValueError as e:
                errors.append(str(e))
        if len(errors) > 0:
            raise ValueError('\n'.join(errors))

    def as_str(self, column_name: str) -> str:
        spec: str = ' AND '.join([spec.as_str(column_name) for spec in self._specs])
        return f'({spec})'


class or_(Specification[T]):
    def __init__(self, *specs: Specification[T]) -> None:
        super().__init__()
        if len(specs) < 2:
            raise ValueError
        self._specs: tuple[Specification[T], ...] = specs

    def check_value(self, value: T, info: dict[str, Any]) -> None:
        errors: list[str] = []
        for spec in self._specs:
            try:
                spec.check_value(value, info)
            except ValueError as e:
                errors.append(str(e))
        if len(errors) == len(self._specs):
            raise ValueError('\n'.join(errors))

    def as_str(self, column_name: str) -> str:
        spec: str = ' OR '.join([spec.as_str(column_name) for spec in self._specs])
        return f'({spec})'


class lt_(Specification[SLT]):
    def __init__(self, ref: Reference[SLT]) -> None:
        super().__init__()
        self._ref = ref

    def check_value(self, value: SLT, info: dict[str, Any]) -> None:
        wrapped: SLT = self._ref.value(info)
        if not wrapped < value:
            raise ValueError(f'Less than check error: value "{value}" is greater or equal than "{wrapped}"')

    def as_str(self, column_name: str) -> str:
        return f'{column_name} < {self._ref.as_str(column_name)}'


class gt_(Specification[SGT]):
    def __init__(self, ref: Reference[SGT]) -> None:
        super().__init__()
        self._ref = ref

    def check_value(self, value: SGT, info: dict[str, Any]) -> None:
        wrapped: SGT = self._ref.value(info)
        if not wrapped > value:
            raise ValueError(f'Greater than check error: value "{value}" is less or equal than "{wrapped}"')

    def as_str(self, column_name: str) -> str:
        return f'{column_name} > {self._ref.as_str(column_name)}'


class ge_(Specification[SGE]):
    def __init__(self, ref: Reference[SGE]) -> None:
        super().__init__()
        self._ref = ref

    def check_value(self, value: SGE, info: dict[str, Any]) -> None:
        wrapped: SGE = self._ref.value(info)
        if not wrapped >= value:
            raise ValueError(f'Greater than equal check error: value "{value}" is less than "{wrapped}"')

    def as_str(self, column_name: str) -> str:
        return f'{column_name} >= {self._ref.as_str(column_name)}'


class le_(Specification[SLE]):
    def __init__(self, ref: Reference[SLE]) -> None:
        super().__init__()
        self._ref = ref

    def check_value(self, value: SLE, info: dict[str, Any]) -> None:
        wrapped: SLE = self._ref.value(info)
        if not wrapped <= value:
            raise ValueError(f'Less than equal check error: value "{value}" is greater than "{wrapped}"')

    def as_str(self, column_name: str) -> str:
        return f'{column_name} <= {self._ref.as_str(column_name)}'


# f'Check predicate types must be compatible "{source!r}"'
# f'Value "{value!r}" invalid for field "{info.field_name}"'
class eq_(Specification[SEQ]):
    def __init__(self, ref: Reference[SEQ]) -> None:
        super().__init__()
        self._ref = ref

    def check_value(self, value: SEQ, info: dict[str, Any]) -> None:
        wrapped: SEQ = self._ref.value(info)
        if not wrapped == value:
            raise ValueError(f'Equal check error: value "{value}" is not equal to "{wrapped}"')

    def as_str(self, column_name: str) -> str:
        return f'{column_name} = {self._ref.as_str(column_name)}'


class ne_(Specification[SNE]):
    def __init__(self, ref: Reference[SNE]) -> None:
        super().__init__()
        self._ref = ref

    def check_value(self, value: SNE, info: dict[str, Any]) -> None:
        wrapped: SNE = self._ref.value(info)
        if not wrapped != value:
            raise ValueError(f'Not equal check error: value "{value}" is equal to "{wrapped}"')

    def as_str(self, column_name: str) -> str:
        return f'{column_name} <> {self._ref.as_str(column_name)}'


class attr_(Specification[T], Generic[T, V]):
    def __init__(self, to_call: Attribute[T, V], spec: Specification[V]):
        super().__init__()
        self._to_call = to_call
        self._spec = spec

    def check_value(self, value: T, info: dict[str, Any]) -> None:
        try:
            self._spec.check_value(self._to_call(value), info)
        except ValueError as e:
            raise ValueError(f'Attribute "{self._to_call}" error:\n{str(e)}')

    def as_str(self, column_name: str) -> str:
        left_operand: str = self._to_call.as_str(column_name)
        return self._spec.as_str(left_operand)


class pg_meta:
    @dataclass
    class index:
        name: str
        type: pg_table_index_type = pg_table_index_type.BTREE

    @dataclass
    class unique_index:
        name: str
        type: pg_table_index_type = pg_table_index_type.BTREE

    @dataclass
    class primary_key:
        name: str

    @dataclass(kw_only=True)
    class foreign_key:
        name: str
        other_class: type[pg_table]
        other_class_column_name: str
        on_update: pg_table_foreign_key_action = pg_table_foreign_key_action.NO_ACTION
        on_delete: pg_table_foreign_key_action = pg_table_foreign_key_action.NO_ACTION

        def __get_pydantic_core_schema__(self, source: Type[T], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            errors: list[str] = []
            if not issubclass(self.other_class, pg_table):
                errors.append(f'Other class {self.other_class} must be a {pg_table} instance')
            if self.other_class_column_name not in self.other_class.model_fields:
                errors.append(f'Foreign key column {self.other_class_column_name} must exist in {self.other_class} definition')
            other_class_column: FieldInfo = self.other_class.model_fields[self.other_class_column_name]
            schema: core_schema.CoreSchema = handler(source)
            if extract_type(other_class_column.annotation) != extract_type(source):
                errors.append(f'Foreign key column {handler.field_name} type must match with {self.other_class_column_name} in {self.other_class} definition')
            if len(errors) > 0:
                raise TypeError(', '.join(errors))
            # ignore class pg_meta.check[T] has no attribute __orig_class__ error
            # raised by mypy
            return schema

    @dataclass
    class comment:
        content: str

    @dataclass(kw_only=True)
    class check(Generic[T]):
        predicate: Specification[T]
        name: str

        def __get_pydantic_core_schema__(self, source: Type[T], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            if self.predicate is None:
                raise ValueError('Check predicate cannot be empty')
            # if not isinstance(source, pg_table) and not isinstance(source, pg_composite):
                # raise ValueError(f'Meta {source.__name__} must be used on a pg_table or a pg_composite instance field')
            schema = handler(source)
            # ignore class pg_meta.check[T] has no attribute __orig_class__ error
            # raised by mypy
            self.predicate.check_type(source, get_args(self.__orig_class__)[0])
            return core_schema.with_info_after_validator_function(
                function=self.validate,
                schema=schema,
                field_name=handler.field_name)

        def validate(self, value: T, info: ValidationInfo) -> T:
            self.predicate.check_value(value, info.data)
            return value

        def merge(self, other: list['check']) -> Self:
            if len(other) <= 0:
                return self
            self.predicate = and_(self.predicate, *tuple(other))
            return self

    class default:
        @dataclass
        class value(Generic[T]):
            content: T

            def __get_pydantic_core_schema__(self, source: Type[T], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
                base: type = get_args(self.__orig_class__)[0]
                errors: list[str] = []
                if not is_optional(source):
                    errors.append('Annotated type must be optional')
                if base not in get_args(source):
                    errors.append('Base type must match annotated type')
                if len(errors) > 0:
                    raise TypeError(', '.join(errors))
                # ignore class pg_meta.check[T] has no attribute __orig_class__ error
                # raised by mypy
                return core_schema.with_info_after_validator_function(
                    function=self.validate,
                    schema=handler(source),
                    field_name=handler.field_name)

            def validate(self, value: Optional[T], info: ValidationInfo) -> T:
                if value is None:
                    return self.content
                return value

            @staticmethod
            def consistent_list(elems: list['pg_meta.default.value']) -> bool:
                if len(elems) <= 0:
                    return True
                initial: pg_meta.default.value = elems[0]
                consistent: bool = True
                for elem in elems:
                    consistent = consistent and elem.value == initial.value
                return consistent

        @dataclass
        class nextval:
            seq: pg_sequence

            def __get_pydantic_core_schema__(self, source: type, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
                base_seq: type = self.seq.__bases__[0]
                errors: list[str] = []
                if is_optional(source):
                    errors.append('Annotated type must not be optional')
                if base_seq is not source:
                    errors.append('Sequence type must match annotated type')
                if len(errors) > 0:
                    raise TypeError(', '.join(errors))
                # ignore class pg_meta.check[T] has no attribute __orig_class__ error
                # raised by mypy
                return core_schema.with_info_after_validator_function(
                    function=self.validate,
                    schema=handler(source),
                    field_name=handler.field_name)

            def validate(self, value: Any, info: ValidationInfo) -> Any:
                if value is None:
                    raise ValueError(f'Sequence {self.seq.__name__} value cant be empty')
                return value

            @staticmethod
            def consistent_list(elems: list['pg_meta.default.nextval']):
                if len(elems) <= 0:
                    return True
                initial: pg_meta.default.nexval = elems[0]
                consistent: bool = True
                for elem in elems:
                    consistent = consistent and elem.seq.__name__ != initial.seq.__name__
                return consistent


def with_pg_comment(comment: pg_meta.comment) -> Callable[type, type]:
    """
    Comments can be inserted into all types
    """

    def inject_comment(wrapped_cls: type) -> type:
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)

        @classmethod
        def __pg_comment(cls) -> pg_meta.comment:
            return comment

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__pg_comment': __pg_comment})
    return inject_comment


def with_pg_check(check: pg_meta.check) -> Callable[type, type]:
    """
    Checks can be inserted into domains
    """

    def inject_check(wrapped_cls: type) -> type:
        if not isinstance(wrapped_cls, pg_domain):
            raise Exception('Check decorators can only be applied on domains.')

        clsname: str = wrapped_cls.__name__
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)
        clsdict = dict(wrapped_cls.__dict__)

        def __new__(cls, *args, **kwargs):
            check.predicate.check_value(args[0], clsdict)
            return bases[0].__new__(bases[0], *args)

        @classmethod
        def __get_pydantic_core_schema__(cls, *args, **kwargs) -> core_schema.CoreSchema:
            return check._check__get_pydantic_core_schema__(*args, **kwargs)

        @classmethod
        def __pg_check(cls) -> pg_meta.check:
            return check

        return type(clsname, bases, clsdict | {
            '__new__': __new__,
            '__get_pydantic_core_schema__': __get_pydantic_core_schema__,
            '__pg_check': __pg_check})
    return inject_check


class with_pg_max_value(Generic[T]):
    def __init__(self, max_value: T):
        self._max_value = max_value

    def __call__(self, wrapped_cls) -> type:
        if not isinstance(wrapped_cls, pg_sequence):
            raise Exception('Decorated class must be a sequence')
        wrapped_cls_base: type = wrapped_cls.__bases__[0]
        type_arg: type = get_args(self.__orig_class__)[0]
        if wrapped_cls_base is not type_arg:
            raise Exception(f'Class {wrapped_cls} base class must match with {type(type_arg)}')

        @classmethod
        def __pg_max_value(cls) -> T:
            return self._max_value
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__pg_max_value': __pg_max_value})


class with_pg_min_value(Generic[T]):
    def __init__(self, max_value: T):
        self._max_value = max_value

    def __call__(self, wrapped_cls) -> type:
        if not isinstance(wrapped_cls, pg_sequence):
            raise Exception('Decorated class must be a sequence')
        wrapped_cls_base: type = wrapped_cls.__bases__[0]
        type_arg: type = get_args(self.__orig_class__)[0]
        if wrapped_cls_base is not type_arg:
            raise Exception(f'Class {wrapped_cls} base class must match with {type(type_arg)}')

        @classmethod
        def __pg_min_value(cls) -> T:
            return self._max_value
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls) # should use mro instead

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__pg_min_value': __pg_min_value})
