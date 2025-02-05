from typing import\
    Any,\
    TypeVar,\
    Generic
from typing import\
    Type
from ..common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowNode,\
    DefinitionFlowBuilder,\
    FlowException,\
    NodeException,\
    execute_definition_flow
from ..common.node import\
    CommonDetermineIfObjectIsDomainNode
from .schema import\
    schema
from .sequence import\
    sequence
from ..metaclasses.table import\
    table
from ..metaclasses.builtin import\
    builtin
from ..metaclasses.composite import\
    composite
from ..metaclasses.enums import\
    enum
from .function import\
    function
from .comment import\
    add_comment


__all__ = ['permission']


_permission_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('permission-definition-flow')
permission_definition_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_permission_definition_flow_root)


# a permission is a direct descendant of a permission, and inherits only from permission
# a role groups several permissions. Roles cant inherit from another roles
class _permission(type):
    def __new__(
        cls, clsname: str, clsbases: tuple[type], clsdict: dict[str, Any]
    ) -> type:
        rettype: type = super().__new__(
            cls, clsname, clsbases, clsdict
        )
        execute_definition_flow(rettype, _permission_definition_flow_root)
        return rettype


T = TypeVar('T', table, sequence, schema, function)


class _Grant(Generic[T]):
    def __init__(self, tp: Type[T]):
        self.tp_def = tp._postgres_definition

    def __call__(self, target: Type[_permission]):
        assert issubclass(target, permission)
        definition: dict[str, Any] = target._postgres_definition
        assert 'type_grants' in definition
        assert definition['kind'] == 'permission'
        self.store_definition(definition)
        return target

    def store_definition(self, definition: dict[str, Any]) -> None:
        grants: dict[str, Any] = definition['type_grants']
        if self.tp_def['type'] not in definition['type_grants']:
            grants[self.tp_def['type']] = {'grants': {}}
        grants[self.tp_def['type']]['grants'][self.__class__.__name__] = True


class permission(metaclass=_permission):
    class add_comment(add_comment):
        pass

    class grant:
        class table:
            class select(_Grant[table]):
                def __init__(self, tp: Type[table]):
                    _Grant.__init__(self, tp)
                    assert isinstance(tp, table)

            class insert(_Grant[table]):
                def __init__(self, tp: Type[table]):
                    _Grant.__init__(self, tp)
                    assert isinstance(tp, table)

            class update(_Grant[table]):
                def __init__(self, tp: Type[table]):
                    _Grant.__init__(self, tp)
                    assert isinstance(tp, table)

            class delete(_Grant[table]):
                def __init__(self, tp: Type[table]):
                    _Grant.__init__(self, tp)
                    assert isinstance(tp, table)

            class truncate(_Grant[table]):
                def __init__(self, tp: Type[table]):
                    _Grant.__init__(self, tp)
                    assert isinstance(tp, table)

            class references(_Grant[table]):
                def __init__(self, tp: Type[table], columns: tuple[str]) -> None:
                    _Grant.__init__(self, tp)
                    assert isinstance(tp, table)
                    assert len(columns) > 0
                    self.columns = columns

                def store_definition(self, definition: dict[str, Any]) -> None:
                    super().store_definition(definition)
                    definition['type_grants'][self.tp_def['type']]['grants'][self.__class__.__name__] = self.columns

        class schema:
            class usage(_Grant[schema]):
                def __init__(self, tp: Type[schema]):
                    _Grant.__init__(self, tp)
                    assert issubclass(tp, schema)

            class create(_Grant[schema]):
                def __init__(self, tp: Type[schema]):
                    _Grant.__init__(self, tp)
                    assert issubclass(tp, schema)

        class sequence:
            class usage(_Grant[sequence]):
                def __init__(self, tp: Type[sequence]):
                    _Grant.__init__(self, tp)
                    assert issubclass(tp, sequence)

            class select(_Grant[sequence]):
                def __init__(self, tp: Type[sequence]):
                    _Grant.__init__(self, tp)
                    assert issubclass(tp, sequence)

            class update(_Grant[sequence]):
                def __init__(self, tp: Type[sequence]):
                    _Grant.__init__(self, tp)
                    assert issubclass(tp, sequence)

        class function:
            class execute(_Grant[function]):
                def __init__(self, tp: Type[function]):
                    _Grant.__init__(self, tp)
                    assert issubclass(tp, function)

        class type:
            class usage(_Grant[sequence]):
                def __init__(self, tp: Type[sequence]):
                    _Grant.__init__(self, tp)
                    assert issubclass(tp, composite) or issubclass(tp, enum) or isinstance(tp, builtin)


class _PermissionDetermineIfTargetIsRoleNode(CommonDetermineIfObjectIsDomainNode):
    def __init__(self):
        super().__init__('permission-determine-if-target-is-domain-node', permission)

    def get_next(self, accumulator: FlowAccumulator) -> DefinitionFlowNode:
        try:
            if self.is_domain:
                return self._nodes['role-validate-base-classes-node']
            return self._nodes['permission-validate-base-class-node']
        except KeyError as e:
            raise FlowException(f'Choice not found in node {self.name}: {str(e)}')


class _PermissionValidateBaseClassNode(SingleChoiceDefinitionFlowNode):
    """
    We must ensure that target definition inherits from classes with the same 
    base class.
    """

    def __init__(self):
        super().__init__('permission-validate-base-class-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        if len(target.__bases__) > 1:
            errors.append(f'Permission {target} cant inherit from more than one base class')
        if target.__bases__[0] is not permission:
            errors.append(f'Permission {target} must inherit from permission directly')
        if len(errors) > 0:
            raise NodeException(self.name, errors)


class _PermissionStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('permission-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = dict()
        definition['type'] = target
        definition['comment'] = None
        definition['kind'] = 'permission'
        definition['type_grants'] = {}
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('permission-validate-base-class-node', )


class _RoleValidateBaseClassesNode(SingleChoiceDefinitionFlowNode):
    """
    We must ensure that roles do not inherit from another role
    """

    def __init__(self):
        super().__init__('role-validate-base-classes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for base_class in target.__bases__:
            if not issubclass(base_class, permission):
                errors.append(f'Base class {base_class} must be a permission subclass')
                continue
            if base_class is permission:
                errors.append(f'Role cant have {base_class} as a base class')
                continue
            base_definition: dict[str, Any] = base_class._postgres_definition
            if base_definition['kind'] == 'role':
                errors.append(f'Base class {base_class} must be a permission, not a role')
                continue
        if len(errors) > 0:
            raise NodeException(self.name, errors)


class _RoleStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('role-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = dict()
        definition['type'] = target
        definition['comment'] = None
        definition['schema'] = None
        definition['kind'] = 'role'
        definition['permissions'] = tuple(target.__bases__)
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('role-validate-base-classes-node', )


permission_definition_flow_builder\
    .at_work_path('')\
    .add_node(_PermissionDetermineIfTargetIsRoleNode)\
    .build_choice(_PermissionValidateBaseClassNode)\
        .add_node(_PermissionStoreFinalDefinitionNode).critical()\
        .end_choice()\
    .build_choice(_RoleValidateBaseClassesNode)\
        .add_node(_RoleStoreFinalDefinitionNode).critical()\
        .end_choice()

