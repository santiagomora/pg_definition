from typing import\
    Any,\
    Optional
from .common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowBuilder,\
    NodeException,\
    execute_definition_flow
from .builtin import\
    bigint,\
    smallint,\
    integer,\
    builtin


__all__ = ['bigint_sequence', 'integer_sequence', 'smallint_sequence']


_sequence_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('sequence-definition-flow')
sequence_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_sequence_definition_flow_root)


class sequence(builtin):
    def __new__(
        cls, clsname: str, clsbases: tuple[type],
        clsdict: dict[str, Any], **kwargs
    ) -> type:
        if len(clsbases) > 1:
            raise TypeError(f'Class {cls} doesnt allow multiple bases')
        try:
            allowed_bases: tuple[type, ...] = (bigint_sequence, integer_sequence, smallint_sequence, )
            if clsbases[0] not in allowed_bases:
                raise TypeError(f'Class {clsname} must be a subclass of any of these classes {allowed_bases}')
        except NameError:
            pass
        rettype: type = super()\
            .__new__(cls, clsname, clsbases, clsdict)
        execute_definition_flow(rettype, _sequence_definition_flow_root)
        return rettype


class _SequenceValidateBaseClassesClassNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('sequence-validate-base-classes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        base_cls_count: dict[type, int] = {}
        for base_cls in target.mro():
            base_cls_count[base_cls] = base_cls_count.get(base_cls, 0) + 1
        appearance_count = sum([base_cls_count.get(tp, 0) for tp in (integer, bigint, smallint, )])
        if appearance_count > 1:
            raise NodeException(f'Sequence cant inherit from more than one {integer}, {bigint} or {smallint}')


class _SequenceExtractBaseTypeNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('sequence-extract-base-type-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        extracted: Optional[type] = None
        for base_cls in target.mro():
            if base_cls in (integer, bigint, smallint, ):
                extracted = base_cls
                break
        accumulator.add_definition('base_type', extracted)

    def get_dependencies(self) -> tuple[str]:
        return ('sequence-validate-base-classes-node', )


class _SequenceStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('sequence-store-final-definition-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = dict()
        definition['base_type'] = accumulator.get_definition('base_type', 'extraction')
        definition['comment'] = None
        definition['min_value'] = None
        definition['max_value'] = None
        definition['increment'] = None
        definition['cycle'] = None
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('sequence-extract-base-type-node', )


sequence_flow_builder\
    .at_work_path('validation')\
        .add_node(_SequenceValidateBaseClassesClassNode)\
    .at_work_path('extraction')\
        .add_node(_SequenceExtractBaseTypeNode)\
    .at_work_path('')\
        .add_node(_SequenceStoreFinalDefinitionNode)


class bigint_sequence(bigint, metaclass=sequence):
    pass


class integer_sequence(integer, metaclass=sequence):
    pass


class smallint_sequence(smallint, metaclass=sequence):
    pass
