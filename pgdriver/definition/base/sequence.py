from typing import\
    Generic,\
    get_args,\
    TypeVar
from .common.flow import\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    DefinitionFlowBuilder
from .builtin import\
    pg_bigint,\
    pg_smallint,\
    pg_int


_pg_sequence_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('sequence-definition-flow')
sequence_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_pg_sequence_definition_flow_root)


T = TypeVar('T', bound=int)


class pg_sequence(type, Generic[T]):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        accumulator: FlowAccumulator = FlowAccumulator(cls)
        _pg_sequence_definition_flow_root.execute(cls, accumulator)


class _SequenceValidateTargetTypeNode(SingleChoiceDefinitionFlowNode):
    """
    target type must be an instance of pg_int, pg_bigint or pg_smallint
    """

    def __init__(self):
        super().__init__('validate-target-type-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        pass
        # if target is pg_bigint or target is pg_int or target is pg_smallint:
        #     return
        # raise FlowNodeException(self.name, [f'Target type {type} must be a pg_bigint, pg_int or a pg_smallint instance'])


class _SequenceStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
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
        bases: tuple[type] = wrapped_cls.__bases__

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
        bases: tuple[type] = wrapped_cls.__bases__

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__pg_min_value': __pg_min_value})


sequence_flow_builder\
    .at_work_path('validation')\
        .add_node(_SequenceValidateTargetTypeNode)\
    .at_work_path('')\
        .add_node(_SequenceStoreFinalDefinitionNode)


class pg_bigint_sequence(pg_sequence[pg_bigint]):
    pass


class pg_int_sequence(pg_sequence[pg_int]):
    pass


class pg_smallint_sequence(pg_sequence[pg_smallint]):
    pass


__all__ = {
    'with_pg_max_value': with_pg_max_value,
    'with_pg_min_value': with_pg_min_value}
