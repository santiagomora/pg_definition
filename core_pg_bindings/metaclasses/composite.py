from typing import\
    Any,\
    Optional
from ..common.flow import\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator,\
    FlowException,\
    NodeException,\
    DefinitionFlowNode,\
    DefinitionFlowBuilder,\
    RootDefinitionFlowNode,\
    execute_definition_flow
from .builtin import\
    builtin,\
    compound
import core_types as bt
from core_pg_bindings.objects.comment import\
    comment,\
    add_comment,\
    add_field_comment
from ..common.node import\
    CommonDetermineIfTargetIsDomainNode
from ..common.inspection import\
    extract_definition_fields,\
    extract_first_instance_from_field_metadata
from ..common.inspection import\
    check_tp_is_domain,\
    check_tp_is_not_domain
import inspect


__all__ = ['composite']


composite_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('composite-definition-flow')
composite_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(composite_definition_flow_root)


class CompositeOperandDefinitionContext(bt.OperandDefinitionContext):
    @classmethod
    def parse_field(cls, field_instance: bt.field) -> str:
        return f'(VALUE).{field_instance._fieldname}'

    @classmethod
    def parse_this(cls, this_instance: bt.this) -> str:
        if this_instance._fieldname is None:
            raise ValueError(f'Operand {repr(this_instance)} definition not correctly propagated.')
        return f'(VALUE).{this_instance._fieldname}'


class composite(compound):
    class add_comment(add_comment):
        pass

    class add_attribute_comment(add_field_comment):
        def __init__(self, *, attribute: str, value: str):
            return super().__init__(field_name=attribute, value=value, accessor='attributes')

        def __call__(self, target: type) -> type:
            check_tp_is_not_domain(target)
            return super().__call__(target)

    class set_default(builtin.set_default):
        pass

    class set_check_constraint(compound.set_constraint):
        def __init__(
            self, *, attribute: str, name: str, constraint: bt.LogicOperand
        ) -> None:
            constraint.name = name
            return super().__init__(
                field_name=attribute, constraint=constraint, accessor='attributes'
            )

        def __call__(self, target: type) -> type:
            check_tp_is_domain(target)
            return super().__call__(target)

    def __new__(
        cls, clsname, clsbases, namespace
    ) -> type:
        rettype: type = super().__new__(cls, clsname, clsbases, namespace)
        execute_definition_flow(rettype, composite_definition_flow_root)
        return rettype

    def definition_context(self) -> type[bt.OperandDefinitionContext]:
        return CompositeOperandDefinitionContext


class _CompositeExtractAttributesDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('composite-extract-attributes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de atributos
        attributes: dict[str, dict[str, Any]] = {}
        for name, info in extract_definition_fields(target):
            attributes[name] = {
                'name': name,
                'type': info.annotation,
                'comment': None}
        if len(attributes) <= 0:
            raise NodeException(self.name, [f'Class {target} must declare attributes.'])
        accumulator.add_definition('attributes', attributes)


class _CompositeStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('composite-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, str] = dict()
        definition['type'] = target
        definition['attributes'] = accumulator.get_definition('attributes', 'extraction')
        definition['comment'] = None
        definition['schema'] = inspect.getmodule(target)
        definition['kind'] = 'composite'
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('composite-extract-attributes-node', )


class _CompositeDetermineIfTargetIsDomainNode(CommonDetermineIfTargetIsDomainNode):
    def __init__(self):
        super().__init__('composite-determine-if-target-is-domain-node')

    def get_next(self, accumulator: FlowAccumulator) -> DefinitionFlowNode:
        try:
            if self.is_domain:
                return self._nodes['composite-domain-extract-attributes-node']
            return self._nodes['composite-extract-attributes-node']
        except KeyError as e:
            raise FlowException(f'Choice not found in node {self.name}: {str(e)}')


class _CompositeDomainExtractAttributesDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Extract composite attributes
    """

    def __init__(self):
        super().__init__('composite-domain-extract-attributes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de atributos
        attributes: dict[str, dict[str, Any]] = {}
        for name, info in extract_definition_fields(target):
            attributes[name] = {
                'name': name,
                'type': info.annotation,
                'check': None}
        accumulator.add_definition('attributes', attributes)


class _CompositeDomainStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('composite-domain-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = dict()
        definition['schema'] = inspect.getmodule(target)
        definition['type'] = target
        definition['base_type'] = target.__bases__[0]
        definition['comment'] = None
        definition['kind'] = 'domain'
        definition['check'] = None
        definition['attributes'] = accumulator.get_definition('attributes', 'extraction')
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('composite-domain-extract-attributes-node', )


composite_flow_builder\
    .at_work_path('extraction')\
    .add_node(_CompositeDetermineIfTargetIsDomainNode)\
    .build_choice(_CompositeExtractAttributesDefinitionNode)\
        .at_work_path('')\
        .add_node(_CompositeStoreFinalDefinitionNode).critical()\
        .end_choice()\
    .build_choice(_CompositeDomainExtractAttributesDefinitionNode)\
        .at_work_path('')\
        .add_node(_CompositeDomainStoreFinalDefinitionNode).critical()\
        .end_choice()
