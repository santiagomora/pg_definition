from __future__ import\
    annotations
from abc import\
    ABC,\
    abstractmethod
from dataclasses import\
    dataclass
from typing import\
    Any,\
    Type,\
    TypeVar,\
    Union,\
    Optional,\
    Generic,\
    Callable,\
    Sized
from pydantic_core import\
    core_schema
from pydantic import\
    GetCoreSchemaHandler,\
    ValidationInfo
from pydantic import\
    BaseModel
from functools import\
    reduce
from psycopg import\
    sql
from typing_extensions import\
    Self
from enum import \
    Enum,\
    auto


class OperandDefinitionContext(Enum):
    BUILTIN_DOMAIN = auto()
    COMPOSITE_DOMAIN = auto()
    TABLE = auto()


# TODO this whole module will eventually be cythonized


T = TypeVar('T')


class Operand(Generic[T]):
    @abstractmethod
    def merge(self, operation_cls: type[T], other: Operand[T]) -> Operand[T]:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def value(self, value: Any, info: dict[str, Any]) -> T:
        pass

    @abstractmethod
    def propagate_definition(
        self, basecls: type, fieldname: Optional[str],
        context: OperandDefinitionContext
    ) -> Self:
        pass


class LogicOperand(Operand[bool]):
    def merge(self, operation_cls: type, other: Operand[bool]) -> Operand[bool]:
        if operation_cls == self.__class__:
            self.append(other)
            return self
        else:
            return operation_cls(self, other)

    def check_type(self, annotated_type: type, check_type: type,
                   type_compatibility: dict[type, type]) -> None:
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

    def __and__(self, other: LogicOperand) -> LogicOperand:
        return self.merge(_and, other)

    def __or__(self, other: LogicOperand) -> LogicOperand:
        return self.merge(_or, other)


class ArithmeticOperand(Operand[Any]):
    def merge(self, operation_cls: type, other: Operand[Any]) -> Operand[Any]:
        other.apply_parentheses_as_righthand_operand(operation_cls)
        self.apply_parentheses_as_lefthand_operand(operation_cls)
        return self.merge_in_operation(operation_cls, other)

    def apply_parentheses_as_righthand_operand(self, operation_cls: type) -> None:
        pass

    def apply_parentheses_as_lefthand_operand(self, operation_cls: type) -> None:
        pass

    def merge_in_operation(self, operation_cls: type, other: Operand[T]) -> Operand[T]:
        if operation_cls == self.__class__:
            self.append(other)
            return self
        else:
            return operation_cls(self, other)

    def __add__(self, other: ArithmeticOperand) -> ArithmeticOperand:
        return self.merge(_add, other)

    def __sub__(self, other: ArithmeticOperand) -> ArithmeticOperand:
        return self.merge(_sub, other)

    def __mul__(self, other: ArithmeticOperand) -> ArithmeticOperand:
        return self.merge(_mul, other)

    def __truediv__(self, other: ArithmeticOperand) -> ArithmeticOperand:
        return self.merge(_div, other)

    def __mod__(self, other: ArithmeticOperand) -> ArithmeticOperand:
        return self.merge(_mod, other)

    def __ge__(self, other: ArithmeticOperand) -> LogicOperand:
        return self.merge(_ge, other)

    def __gt__(self, other: ArithmeticOperand) -> LogicOperand:
        return self.merge(_gt, other)

    def __le__(self, other: ArithmeticOperand) -> LogicOperand:
        return self.merge(_le, other)

    def __lt__(self, other: ArithmeticOperand) -> LogicOperand:
        return self.merge(_lt, other)

    def __eq__(self, other: ArithmeticOperand) -> LogicOperand:
        return self.merge(_eq, other)

    def __ne__(self, other: ArithmeticOperand) -> LogicOperand:
        return self.merge(_ne, other)


class ArithmeticOperation(ArithmeticOperand, list[ArithmeticOperand]):
    def __init__(self, operand1: ArithmeticOperand,
                 operand2: ArithmeticOperand, opstr: str) -> None:
        super().__init__((operand1, operand2))
        self.opstr = opstr
        self.parentheses = False

    def __str__(self) -> str:
        as_str: str = f' {self.opstr} '.join([
            str(operand) for operand in self
        ])
        return f'({as_str})' if self.parentheses else as_str

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({", ".join([\
            repr(operand) for operand in self\
        ])})'

    def propagate_definition(
        self, basecls: type, fieldname: Optional[str],
        context: OperandDefinitionContext
    ) -> Self:
        for operand in self:
            operand.propagate_definition(basecls, fieldname, context)
        return self

    @abstractmethod
    def value(self, value: Any, info: dict[str, Any]) -> Any:
        pass


class LogicOperandSpec(LogicOperand):
    def __init__(self, operand1: ArithmeticOperand,
                 operand2: ArithmeticOperand, opstr: str) -> None:
        self.operand1 = operand1
        self.operand2 = operand2
        self.opstr = opstr

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.operand1)}, {repr(self.operand2)})'

    def __str__(self) -> str:
        op1str = str(self.operand1)
        op2str = str(self.operand2)
        if isinstance(self.operand1, ArithmeticOperation):
            op1str = f'({op1str})'
        if isinstance(self.operand2, ArithmeticOperation):
            op2str = f'({op2str})'
        return f'{op1str} {self.opstr} {op2str}'

    def propagate_definition(
        self, basecls: type, fieldname: Optional[str],
        context: OperandDefinitionContext
    ) -> Self:
        self.operand1.propagate_definition(basecls, fieldname, context)
        self.operand2.propagate_definition(basecls, fieldname, context)
        return self


class LogicOperation(LogicOperand, list[LogicOperandSpec]):
    def __init__(self, operand1: LogicOperand, operand2: LogicOperand,
                 opstr: str) -> None:
        super().__init__((operand1, operand2))
        self.opstr = opstr

    def __str__(self) -> str:
        return f' {self.opstr} '.join([
            f'({str(operand)})' for operand in self
        ])

    def __repr__(self):
        return f'{self.__class__.__name__}({", ".join(repr(op) for op in self)})'

    def propagate_definition(
        self, basecls: type, fieldname: Optional[str],
        context: OperandDefinitionContext
    ) -> Self:
        for op in self:
            op.propagate_definition(basecls, fieldname, context)
        return self


class this(ArithmeticOperand):
    def __init__(self) -> None:
        # el field debe ser un atributo de la clase que registra la anotacion
        self._fieldname: Optional[str] = None
        self._context: Optional[OperandDefinitionContext] = None

    def __str__(self) -> str:
        if self._context == OperandDefinitionContext.BUILTIN_DOMAIN:
            return 'VALUE'
        else:
            if self._fieldname is None:
                raise ValueError(f'Operand {repr(self)} definition not correctly propagated.')
            if self._context == OperandDefinitionContext.TABLE:
                return f'{self._fieldname}'
            elif self._context == OperandDefinitionContext.COMPOSITE_DOMAIN:
                return f'(VALUE).{self._fieldname}'
            else:
                raise ValueError(f'Invalid operand {repr(self)} definition context')

    def __repr__(self) -> str:
        if self._fieldname is not None:
            return f"this(fieldname={self._fieldname}, context={self._context})"
        else:
            return 'this()'

    def value(self, value: Any, info: dict[str, Any]) -> Any:
        return value

    def propagate_definition(
        self, basecls: type, fieldname: Optional[str],
        context: OperandDefinitionContext
    ) -> Self:
        self._fieldname = fieldname
        self._context = context
        return self


class field(ArithmeticOperand):
    def __init__(self, fieldname: str) -> None:
        # el field debe ser un atributo de la clase que registra la anotacion
        self._fieldname: str = fieldname

    def value(self, value: Any, info: dict[str, Any]) -> Any:
        # info tiene un atributo data con los datos validos del modelo
        # para poder validar la dependencia entre dos campos
        # es necesario que el campo que define la relacion aparezca
        # despues del objetivo en la definicion del modelo
        return info[self._fieldname]

    def __repr__(self):
        return f'field({self._fieldname})'

    def __str__(self) -> str:
        return f'(VALUE).{self._fieldname}'

    def propagate_definition(
        self, basecls: type, fieldname: Optional[str],
        context: OperandDefinitionContext
    ) -> Self:
        return self


class literal(ArithmeticOperand):
    def __init__(self, *args: Any, **kwargs: dict[str, Any]) -> None:
        self._args = args
        self._kwargs = kwargs
        self._lit = None

    def __str__(self):
        return f'{self._lit if self._lit is not None else self._args[0]}'

    def __repr__(self):
        return f'literal({repr(self._lit)})'

    def value(self, value: Any, info: dict[str, Any]) -> Any:
        return self._args[0] if self._lit is None else self._lit

    def propagate_definition(
        self, basecls: type, fieldname: Optional[str],
        context: OperandDefinitionContext
    ) -> Self:
        if not isinstance(self._lit, basecls):
            self._lit = basecls(*self._args, **self._kwargs)
        return self


class length(ArithmeticOperand):
    def __init__(self, target: ArithmeticOperand) -> None:
        self.target = target

    def __str__(self):
        return f'length({str(self.target)})'

    def __repr__(self):
        return f'length({repr(self.target)})'

    def value(self, value: Any, info: dict[str, Any]) -> Any:
        return len(self.target.value(value, info))

    def propagate_definition(
        self, basecls: type, fieldname: Optional[str],
        context: OperandDefinitionContext
    ) -> Self:
        self.target.propagate_definition(basecls, fieldname, context)
        return self


class _add(ArithmeticOperation):
    def __init__(self, operand1: ArithmeticOperand,
                 operand2: ArithmeticOperand) -> None:
        super().__init__(operand1, operand2, '+')

    def value(self, value: Any, info: dict[str, Any]) -> Any:
        return reduce(lambda x, y: x + y.value(value, info), self[1:], self[0].value(value, info))

    def apply_parentheses_as_lefthand_operand(self, opcls: type) -> None:
        self.parentheses = opcls in (_div, _mul, _mod)

    def apply_parentheses_as_righthand_operand(self, opcls: type) -> None:
        self.parentheses = opcls in (_div, _mul, _mod, _sub)


class _sub(ArithmeticOperation):
    def __init__(self, operand1: ArithmeticOperand,
                 operand2: ArithmeticOperand) -> None:
        super().__init__(operand1, operand2, '-')

    def value(self, value: Any, info: dict[str, Any]) -> Any:
        return reduce(lambda x, y: x - y.value(value, info), self[1:], self[0].value(value, info))

    def apply_parentheses_as_lefthand_operand(self, opcls: type) -> None:
        self.parentheses = opcls in (_div, _mul, _mod)

    def apply_parentheses_as_righthand_operand(self, opcls: type) -> None:
        self.parentheses = opcls in (_div, _mul, _mod, _sub)


class _mul(ArithmeticOperation):
    def __init__(self, operand1: ArithmeticOperand,
                 operand2: ArithmeticOperand) -> None:
        super().__init__(operand1, operand2, '*')

    def value(self, value: Any, info: dict[str, Any]) -> Any:
        return reduce(lambda x, y: x * y.value(value, info), self[1:], self[0].value(value, info))

    def apply_parentheses_as_righthand_operand(self, opcls: type) -> None:
        self.parentheses = opcls in (_div, _mod)


class _div(ArithmeticOperation):
    def __init__(self, operand1: ArithmeticOperand,
                 operand2: ArithmeticOperand) -> None:
        super().__init__(operand1, operand2, '/')

    def value(self, value: Any, info: dict[str, Any]) -> Any:
        return reduce(lambda x, y: x / y.value(value, info), self[1:], self[0].value(value, info))

    def merge_in_operation(self, operation_cls: type,
                           other: ArithmeticOperand) -> Reference:
        return operation_cls(self, other)

    def apply_parentheses_as_righthand_operand(self, opcls: type) -> None:
        self.parentheses = True

    def apply_parentheses_as_lefthand_operand(self, opcls: type) -> None:
        self.parentheses = True


class _mod(ArithmeticOperation):
    def __init__(self, operand1: ArithmeticOperand,
                 operand2: ArithmeticOperand) -> None:
        super().__init__(operand1, operand2, '%')

    def value(self, value: Any, info: dict[str, Any]) -> Any:
        return reduce(lambda x, y: x % y.value(value, info), self[1:], self[0].value(value, info))

    def merge_in_operation(self, operation_cls: type,
                           other: ArithmeticOperand) -> Reference:
        return operation_cls(self, other)

    def add_operand(self, operation_cls: type, other: Reference) -> Reference:
        return operation_cls(self, other)

    def apply_parentheses_as_righthand_operand(self, opcls: type) -> None:
        self.parentheses = True

    def apply_parentheses_as_lefthand_operand(self, opcls: type) -> None:
        self.parentheses = True


class _lt(LogicOperandSpec):
    def __init__(self, operand1: ArithmeticOperand, operand2: ArithmeticOperand) -> None:
        super().__init__(operand1, operand2, '<')

    def value(self, value: Any, info: dict[str, Any]) -> bool:
        return self.operand1.value(value, info) < self.operand2.value(value, info)


class _gt(LogicOperandSpec):
    def __init__(self, operand1: ArithmeticOperand, operand2: ArithmeticOperand) -> None:
        super().__init__(operand1, operand2, '>')

    def value(self, value: Any, info: dict[str, Any]) -> bool:
        return self.operand1.value(value, info) > self.operand2.value(value, info)


class _ge(LogicOperandSpec):
    def __init__(self, operand1: ArithmeticOperand, operand2: ArithmeticOperand) -> None:
        super().__init__(operand1, operand2, '>=')

    def value(self, value: Any, info: dict[str, Any]) -> bool:
        return self.operand1.value(value, info) >= self.operand2.value(value, info)


class _le(LogicOperandSpec):
    def __init__(self, operand1: ArithmeticOperand, operand2: ArithmeticOperand) -> None:
        super().__init__(operand1, operand2, '<=')

    def value(self, value: Any, info: dict[str, Any]) -> bool:
        return self.operand1.value(value, info) <= self.operand2.value(value, info)


# f'Check predicate types must be compatible "{source!r}"'
# f'Value "{value!r}" invalid for field "{info.fieldname}"'
class _eq(LogicOperandSpec):
    def __init__(self, operand1: ArithmeticOperand, operand2: ArithmeticOperand) -> None:
        super().__init__(operand1, operand2, '==')

    def value(self, value: Any, info: dict[str, Any]) -> bool:
        return self.operand1.value(value, info) == self.operand2.value(value, info)


class _ne(LogicOperandSpec):
    def __init__(self, operand1: ArithmeticOperand, operand2: ArithmeticOperand) -> None:
        super().__init__(operand1, operand2, '!=')

    def value(self, value: Any, info: dict[str, Any]) -> bool:
        return self.operand1.value(value, info) != self.operand2.value(value, info)


class _and(LogicOperation):
    def __init__(self, operand1: LogicOperand, operand2: LogicOperand) -> None:
        super().__init__(operand1, operand2, 'AND')

    def value(self, value: Any, info: dict[str, Any]) -> bool:
        return reduce(lambda x, y: x and y.value(value, info), self[1:], self[0].value(value, info))


class _or(LogicOperation):
    def __init__(self, operand1: LogicOperand, operand2: LogicOperand) -> None:
        super().__init__(operand1, operand2, 'OR')

    def value(self, value: Any, info: dict[str, Any]) -> bool:
        return reduce(lambda x, y: x or y.value(value, info), self[1:], self[0].value(value, info))
