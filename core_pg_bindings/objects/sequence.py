from typing import\
    Any,\
    Optional,\
    Union,\
    get_args,\
    TypeAlias
from ..common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowBuilder,\
    execute_definition_flow
from dataclasses import\
    dataclass
import core_pg_bindings.pg_catalog as pg_catalog
from .comment import\
    add_comment
import inspect


__all__ = ['sequence']


_sequence_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('sequence-definition-flow')
sequence_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_sequence_definition_flow_root)


SequenceAllowedBases: TypeAlias = Union[pg_catalog.int8, pg_catalog.int4, pg_catalog.int2, pg_catalog.int1]


class _sequence(type):
    def __new__(
        cls, clsname: str, clsbases: tuple[type],
        clsdict: dict[str, Any], base: Optional[SequenceAllowedBases]
    ) -> type:

        if len(clsbases) > 1:
            raise TypeError(f'Class {cls} doesnt allow multiple bases')

        def __seq_base__() -> Optional[SequenceAllowedBases]:
            return base

        rettype: type = super().__new__(
            cls, clsname, clsbases, clsdict | {'__seq_base__': __seq_base__}
        )

        try:
            assert sequence is not None
            allowed_bases = get_args(SequenceAllowedBases)
            if not any([issubclass(base, tp) for tp in allowed_bases]):
                raise TypeError(f'Class {clsname} must be any of these classes {allowed_bases}')
            execute_definition_flow(rettype, _sequence_definition_flow_root)
        except NameError:
            pass
        return rettype


class sequence(metaclass=_sequence, base=None):
    class add_comment(add_comment):
        pass

    class max_value:
        def __init__(self, max_value: int):
            self._max_value = max_value

        def __call__(self, wrapped) -> type:
            if not issubclass(wrapped, sequence):
                raise TypeError('Decorated class must be a sequence subclass')
            definition = wrapped._postgres_definition
            assert 'max_value' in definition
            assert definition['max_value'] is None
            definition['max_value'] = wrapped.__seq_base__()(self._max_value)
            return wrapped

    class min_value:
        def __init__(self, min_value: int):
            self._min_value = min_value

        def __call__(self, wrapped) -> type:
            if not issubclass(wrapped, sequence):
                raise TypeError('Decorated class must be a sequence subclass')
            definition = wrapped._postgres_definition
            assert 'min_value' in definition
            assert definition['min_value'] is None
            definition['min_value'] = wrapped.__seq_base__()(self._min_value)
            return wrapped

    class increment:
        def __init__(self, increment: int):
            self._increment = increment

        def __call__(self, wrapped) -> type:
            if not issubclass(wrapped, sequence):
                raise TypeError('Decorated class must be a sequence subclass')
            definition = wrapped._postgres_definition
            assert 'increment' in definition
            assert definition['increment'] is None
            definition['increment'] = wrapped.__seq_base__()(self._increment)
            return wrapped

    @dataclass
    class nextval:
        seq: _sequence


class _SequenceExtractBaseTypeNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('sequence-extract-base-type-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        accumulator.add_definition('base_type', getattr(target, '__seq_base__')())


class _SequenceStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('sequence-store-final-definition-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = dict()
        definition['schema'] = inspect.getmodule(target)
        definition['base_type'] = accumulator.get_definition('base_type', 'extraction')
        definition['comment'] = None
        definition['type'] = target
        definition['kind'] = 'sequence'
        definition['min_value'] = None
        definition['max_value'] = None
        definition['increment'] = None
        definition['cycle'] = None
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('sequence-extract-base-type-node', )


sequence_flow_builder\
    .at_work_path('extraction')\
        .add_node(_SequenceExtractBaseTypeNode)\
    .at_work_path('')\
        .add_node(_SequenceStoreFinalDefinitionNode)
