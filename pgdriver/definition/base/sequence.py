from pgdriver.definition.flows import\
    DefinitionFlow,\
    FlowComponent,\
    FlowAccumulator,\
    FlowComponentException
from pgdriver.definition.build import\
    pg_bigint,\
    pg_smallint,\
    pg_int
from typing import\
    Generic,\
    get_args,\
    TypeVar
from pgdriver.definition.inspection import\
    extract_by_instance_type_from_inherited_classes


pg_sequence_definition_flow: DefinitionFlow = DefinitionFlow('pgdriver-sequence-definition-flow')


class pg_sequence(type):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        accumulator: FlowAccumulator = FlowAccumulator()
        pg_sequence_definition_flow.execute(cls, accumulator)


class pg_bigint_sequence(metaclass=pg_sequence):
    pass


class pg_int_sequence(metaclass=pg_sequence):
    pass


class pg_smallint_sequence(metaclass=pg_sequence):
    pass


class SequenceValidateTargetTypeComponent(FlowComponent):
    """
    target type must be an instance of pg_int, pg_bigint or pg_smallint
    """

    def __init__(self):
        super().__init__('validate-target-type-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        if target is pg_bigint or target is pg_int or target is pg_smallint:
            return
        raise FlowComponentException(self.name, [f'Target type {type} must be a pg_bigint, pg_int or a pg_smallint instance'])


class SequenceStoreFinalDefinitionComponent(FlowComponent):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('store-final-definition-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        accumulator.add_definition('final', {})

    def get_dependencies(self) -> tuple[str]:
        return ('validate-target-type-component', )


T = TypeVar('T')


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


with pg_sequence_definition_flow.at_work_path('validation') as flow:
    flow.register(SequenceValidateTargetTypeComponent())

with pg_sequence_definition_flow.at_work_path('') as flow:
    flow.register(SequenceStoreFinalDefinitionComponent())


__all__ = {
    'pg_bigint_sequence': pg_bigint_sequence,
    'pg_int_sequence': pg_int_sequence,
    'pg_smallint_sequence': pg_smallint_sequence,
    'with_pg_max_value': with_pg_max_value,
    'with_pg_min_value': with_pg_min_value}
