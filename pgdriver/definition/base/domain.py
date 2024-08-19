from .common.flow import\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator
from typing import\
    Optional
from .common.meta import\
    pg_type_check,\
    pg_comment


class DomainExtractCheckConstraintNode(SingleChoiceDefinitionFlowNode):
    """
    Extracts the check constraint as a conjunction of the constraint
    defined in the base type and the constraint defined in the target type
    """

    def _get_check_constraint(self, target: type) -> Optional[pg_type_check]:
        try:
            return getattr(target, f'_{target.__name__}__pg_check')
        except AttributeError:
            return None

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        check: Optional[pg_type_check] = self._get_check_constraint(target)
        parent_check: Optional[pg_type_check] = self._get_check_constraint(target.__bases__[0])
        if check is None:
            if parent_check is not None:
                # add parent check constraint to child
                check = parent_check
        else:
            if parent_check is not None:
                check.set_parent(parent_check)
        # in merge stage we will generate the new schema
        accumulator.add_definition('check', check)


class DomainExtractCommentNode(SingleChoiceDefinitionFlowNode):
    """
    Extracts the check constraint as a conjunction of the constraint
    defined in the base type and the constraint defined in the target type
    """

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        comment: Optional[pg_comment] = None
        try:
            comment = getattr(target, f'_{target.__name__}__pg_comment')
        except AttributeError:
            comment = None
        accumulator.add_definition('comment', comment)


class DomainMergeCheckConstraintNode(SingleChoiceDefinitionFlowNode):
    """
    Merges base type merge check constraint and that defined in target type
    """

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        check: Optional[pg_type_check] = accumulator.get_definition('check', 'extraction')
        if check is None:
            return
        if not hasattr(target, f'_{target.__name__}__pg_check'):
            setattr(target, f'_{target.__name__}__pg_check', check)


class DomainStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition, the base type of the domain
    """

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Optional[str]] = dict()
        definition['type_name'] = target.__name__
        definition['base_type_name'] = getattr(target.__bases__[0], '__pg_definition')()['type_name']
        comment: Optional[pg_comment] = accumulator.get_definition('comment', 'extraction')
        definition['comment'] = None if comment is None else comment.value
        check: Optional[pg_type_check] = accumulator.get_definition('check', 'extraction')
        definition['check'] = None if check is None else {'name': check.name,
                                                          'constraint': check.as_str('VALUE')}
        accumulator.add_definition('final', definition)

