from typing import\
    Any
from .common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowBuilder,\
    execute_definition_flow,\
    NodeException
import os


__all__ = ['schema']


_schema_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('schema-definition-flow')
schema_definition_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_schema_definition_flow_root)


class schema_builtin(type):
    def __new__(
        cls, clsname: str, clsbases: tuple[type],
        clsdict: dict[str, Any], **kwargs
    ) -> type:
        try:
            for base in clsbases:
                if not issubclass(base, schema):
                    raise TypeError(f'Schema base class "{base}" must inherit from {schema}')
        except NameError:
            pass
        rettype: type = super()\
            .__new__(cls, clsname, clsbases, clsdict)
        execute_definition_flow(rettype, _schema_definition_flow_root)
        return rettype


class schema(metaclass=schema_builtin):
    pass


class _SchemaSetSchemaOnMembersNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('schema-set-schema-on-members-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        objects: dict[str, Any] = {}
        errors: list[str] = []
        for name, value in target.__dict__.items():
            if not name.startswith('__'):
                definition: dict[str, Any] = getattr(value, '__pg_definition')()
                definition['schema'] = target
                if value.__name__ in objects:
                    errors.append(f'Schema "{target.__name__}" name conflict: "{target.__name__}" defined more than once')
                else:
                    objects[value.__name__] = value
        if len(errors) > 0:
            raise NodeException(self.name, errors)
        accumulator.add_definition('objects', objects)


class _SchemaStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('schema-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = dict()
        definition['type'] = target
        definition['comment'] = None
        definition['kind'] = 'schema'
        definition['function_path_alias'] = {}
        definition['objects'] = accumulator.get_definition('objects', 'extraction')
        accumulator.add_definition('final', definition)


schema_definition_flow_builder\
    .at_work_path('extraction')\
    .add_node(_SchemaSetSchemaOnMembersNode)\
    .at_work_path('')\
    .add_node(_SchemaStoreFinalDefinitionNode)


class register_function_path_alias:
    def __init__(self, *, alias: str, current_file_path: str, function_path: str) -> None:
        self.name = alias
        self.path = f'{os.path.dirname(os.path.abspath(current_file_path))}/{function_path}'

    def __call__(self, target: type):
        assert issubclass(target, schema)
        definition: dict[str, Any] = getattr(target, '__pg_definition')()
        assert self.name not in definition['function_path_alias']
        definition['function_path_alias'][self.name] = self.path
        return target
