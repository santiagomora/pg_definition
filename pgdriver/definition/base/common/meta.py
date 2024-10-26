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
from ...inspection import\
    is_optional
from pydantic import\
    BaseModel


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


class field_(Reference[T]):
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


class literal_(Reference[T]):
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


class _TypeCompatibility(dict[type, type]):
    def register(self, for_type: type, compatible_with: type) -> None:
        if for_type in self:
            raise Exception(f'Cant overwrite {for_type} compatibility.')
        self[for_type] = compatible_with

    def get_supertype(self, for_type: type) -> Optional[type]:
        for t in self:
            if issubclass(for_type, t):
                return t
        return None


class Predicate(BaseModel, Generic[T]):
    def check_type(self, annotated_type: type, check_type: type, type_compatibility: dict[type, type]) -> None:
        if check_type == annotated_type:
            return
        errors: list[str] = []
        if annotated_type not in type_compatibility:
            annotated_type = type_compatibility.get_supertype(annotated_type)
            if annotated_type is None:
                errors.append(f'Compatibility not configured for type {annotated_type!r}')
        if check_type not in type_compatibility:
            source_type = type_compatibility.get_supertype(check_type)
            if source_type is None:
                errors.append(f'Compatibility not configured for type {annotated_type!r}')
        if len(errors) > 0:
            raise TypeError('Check definition error: ' + ', '.join(errors))
        annotated_compat: type = type_compatibility[annotated_type]
        check_compat: type = type_compatibility[check_type]
        if not (issubclass(annotated_compat, check_compat) or issubclass(check_compat, annotated_compat)):
            raise TypeError(f'Check definition error: types {annotated_type} and {check_type} are not compatible')

    @abstractmethod
    def as_str(self, column_name: str) -> str:
        pass

    @abstractmethod
    def check_value(self, value: Any, info: dict[str, Any]) -> None:
        # valida que el valor value cumpla con el spec
        pass


class and_(Predicate[T]):
    def __init__(self, *specs: Predicate[T]) -> None:
        super().__init__()
        if len(specs) < 2:
            raise ValueError
        self._specs: tuple[Predicate[T], ...] = specs

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
        spec: str = ' AND '.join([f'({spec.as_str(column_name)})' for spec in self._specs])
        return spec


class or_(Predicate[T]):
    def __init__(self, *specs: Predicate[T]) -> None:
        super().__init__()
        if len(specs) < 2:
            raise ValueError
        self._specs: tuple[Predicate[T], ...] = specs

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
        spec: str = ' OR '.join([f'({spec.as_str(column_name)})' for spec in self._specs])
        return spec


class lt_(Predicate[SLT]):
    def __init__(self, ref: Reference[SLT]) -> None:
        super().__init__()
        self._ref = ref

    def check_value(self, value: SLT, info: dict[str, Any]) -> None:
        wrapped: SLT = self._ref.value(info)
        if not value < wrapped:
            raise ValueError(f'Less than check error: value "{value}" is greater or equal than "{wrapped}"')

    def as_str(self, column_name: str) -> str:
        return f'{column_name} < {self._ref.as_str(column_name)}'


class gt_(Predicate[SGT]):
    def __init__(self, ref: Reference[SGT]) -> None:
        super().__init__()
        self._ref = ref

    def check_value(self, value: SGT, info: dict[str, Any]) -> None:
        wrapped: SGT = self._ref.value(info)
        if not value > wrapped:
            raise ValueError(f'Greater than check error: value "{value}" is less or equal than "{wrapped}"')

    def as_str(self, column_name: str) -> str:
        return f'{column_name} > {self._ref.as_str(column_name)}'


class ge_(Predicate[SGE]):
    def __init__(self, ref: Reference[SGE]) -> None:
        super().__init__()
        self._ref = ref

    def check_value(self, value: SGE, info: dict[str, Any]) -> None:
        wrapped: SGE = self._ref.value(info)
        if not value >= wrapped:
            raise ValueError(f'Greater than equal check error: value "{value}" is less than "{wrapped}"')

    def as_str(self, column_name: str) -> str:
        return f'{column_name} >= {self._ref.as_str(column_name)}'


class le_(Predicate[SLE]):
    def __init__(self, ref: Reference[SLE]) -> None:
        super().__init__()
        self._ref = ref

    def check_value(self, value: SLE, info: dict[str, Any]) -> None:
        wrapped: SLE = self._ref.value(info)
        if not value <= wrapped:
            raise ValueError(f'Less than equal check error: value "{value}" is greater than "{wrapped}"')

    def as_str(self, column_name: str) -> str:
        return f'{column_name} <= {self._ref.as_str(column_name)}'


# f'Check predicate types must be compatible "{source!r}"'
# f'Value "{value!r}" invalid for field "{info.field_name}"'
class eq_(Predicate[SEQ]):
    def __init__(self, ref: Reference[SEQ]) -> None:
        super().__init__()
        self._ref = ref

    def check_value(self, value: SEQ, info: dict[str, Any]) -> None:
        wrapped: SEQ = self._ref.value(info)
        if not wrapped == value:
            raise ValueError(f'Equal check error: value "{value}" is not equal to "{wrapped}"')

    def as_str(self, column_name: str) -> str:
        return f'{column_name} = {self._ref.as_str(column_name)}'


class ne_(Predicate[SNE]):
    def __init__(self, ref: Reference[SNE]) -> None:
        super().__init__()
        self._ref = ref

    def check_value(self, value: SNE, info: dict[str, Any]) -> None:
        wrapped: SNE = self._ref.value(info)
        if not wrapped != value:
            raise ValueError(f'Not equal check error: value "{value}" is equal to "{wrapped}"')

    def as_str(self, column_name: str) -> str:
        return f'{column_name} <> {self._ref.as_str(column_name)}'


class attr_(Predicate[T], Generic[T, V]):
    def __init__(self, to_call: Attribute[T, V], spec: Predicate[V]):
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


class pg_check(ABC, Generic[T]):
    type_compatibility: _TypeCompatibility = _TypeCompatibility()

    def __init__(self, *, name: str, predicate: Predicate[T]) -> None:
        self.predicate = predicate
        self.name = name
        self._parent_check: Optional[pg_check] = None
        self._source = None

    def get_parent(self) -> Optional['pg_check']:
        return self._parent_check

    def merge(self, other: 'pg_check') -> 'pg_check':
        self._parent_check = other
        return other

    def as_str(self, field_name: str):
        return f'({self.predicate.as_str(field_name)})'

    def _validate(self, value: T, info_data: Optional[ValidationInfo] = None) -> T:
        data = {} if info_data is None else {}
        try:
            self.predicate.check_value(value, data)
        except ValueError as e:
            raise ValueError(f'{self.name}: {str(e)}')
        if self._parent_check is not None:
            return self._parent_check._validate(value, data)
        return value

    def __get_pydantic_core_schema__(self, source: Type[T],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        self._source = source
        schema = handler(source)
        # ignore class pg_meta.check[T] has no attribute __orig_class__ error
        # raised by mypy
        self.check_valid_constraint_definition(source)
        return core_schema.with_info_after_validator_function(function=self.validate_value,
                                                              schema=schema,
                                                              field_name=handler.field_name)

    def validate_value(self, value: T, info: ValidationInfo) -> T:
        if value is None:
            definition = getattr(self._source, '__pg_definition')()
            value = definition['default_value'] if 'default_value' in definition else value
        return self._validate(value, info.data)

    def check_valid_constraint_definition(self, target: type) -> None:
        # shouldnt propagate to parent as parent check constraint was validated
        # on a different domain, we can assume is valid by now
        self.predicate.check_type(target, get_args(self.__orig_class__)[0],
                                  pg_check.type_compatibility)


@dataclass
class pg_comment:
    value: str


class pg_default_value(Generic[T]):

    def __init__(self, content: T) -> None:
        self.content = content
        self._source = None

    def __get_pydantic_core_schema__(self, source: Type[T],
                                     handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        self._source = source
        # base: type = get_args(self.__orig_bases__)[0]
        # errors: list[str] = []
        # if not is_optional(source):
        #     errors.append('Annotated type must be optional')
        # if base not in get_args(source):
        #     errors.append('Base type must match annotated type')
        # if len(errors) > 0:
        #     raise TypeError(', '.join(errors))
        # # ignore class pg_table_meta.check[T] has no attribute __orig_class__ error
        # # raised by mypy
        return core_schema.with_info_after_validator_function(
            function=self.validate,
            schema=handler(source),
            field_name=handler.field_name)

    def validate(self, value: Optional[T], info: ValidationInfo) -> T:
        if value is None:
            return self.content
        return value
