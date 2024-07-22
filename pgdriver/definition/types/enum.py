from pgdriver.definition.types.metadata import\
    pg_comment
from enum import\
    EnumType
from pgdriver.definition.flow import\
    DefinitionFlow,\
    FlowAccumulator,\
    FlowComponent


class pg_enum(EnumType):
    pass


pgenum_definition_flow: DefinitionFlow[pg_enum] = DefinitionFlow[pg_enum]('pgdriver-enum-definition-flow', pg_enum)


class ExtractCommentDefinitionComponent(FlowComponent[pg_enum]):
    """
    Extract enum comments
    """

    def __init__(self):
        super().__init__('extract-comment-definition-component')

    def execute(self, target: type[pg_enum], accumulator: FlowAccumulator) -> None:
        attr_name: str = f'_{target.__name__}__pg_comment'
        if hasattr(target, attr_name):
            comment: pg_comment = getattr(target, attr_name)()
            accumulator.add_definition('comment', comment.value)


pgenum_definition_flow.register_component(
    ExtractCommentDefinitionComponent())

pgenum_definition_flow.set_critical_component('extract-comment-definition-component')
