from pgdriver.definition.flows import\
    TypeInstanceDefinitionFlow,\
    FlowComponent,\
    FlowAccumulator,\
    FlowComponentException
from pgdriver.definition.build import\
    pg_sequence,\
    pg_bigint,\
    pg_smallint,\
    pg_int


class SequenceDefinitionFlow(TypeInstanceDefinitionFlow[pg_sequence]):
    def __init__(self):
        super().__init__('pgdriver-sequence-definition-flow')


class SequenceValidateTargetTypeComponent(FlowComponent[pg_sequence]):
    """
    target type must be an instance of pg_int, pg_bigint or pg_smallint
    """

    def __init__(self):
        super().__init__('validate-target-type-component')

    def execute(self, target: type[pg_sequence], accumulator: FlowAccumulator) -> None:
        if target is pg_bigint or target is pg_int or target is pg_smallint:
            return
        raise FlowComponentException(self.name, [f'Target type {type} must be a pg_bigint, pg_int or a pg_smallint instance'])


pg_sequence_definition_flow: SequenceDefinitionFlow = SequenceDefinitionFlow()

with pg_sequence_definition_flow.at_work_path('validation') as flow:
    flow.register(SequenceValidateTargetTypeComponent())


__all__ = {'pg_sequence_definition_flow': pg_sequence_definition_flow}
