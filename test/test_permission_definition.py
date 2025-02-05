import pg_definition as pg
from typing import\
    Any
import sys
sys.path.append('./')
import test_app.backend as test_app


def test_permission_definition_flow_detects_invalid_bases() -> None:
    try:
        class test_permission_1(pg.permission):
            pass

        class test_permission_2(pg.permission, str):
            pass
    except pg.FlowException as errors:
        e = errors.get_error('permission-definition-flow', 
                             'permission-validate-base-class-node')
        assert str(e) == "Permission <class 'test_permission_definition.test_permission_definition_flow_detects_invalid_bases.<locals>.test_permission_2'> cant inherit from more than one base class"


def test_role_definition_flow_detects_invalid_bases() -> None:
    try:
        class test_permission_1(pg.permission):
            pass

        class test_permission_2(test_permission_1, str):
            pass
    except pg.FlowException as errors:
        e = errors.get_error('permission-definition-flow', 
                             'role-validate-base-classes-node')
        assert str(e) == f"Base class {str} must be a permission subclass"

    try:
        class test_permission_1(pg.permission):
            pass

        class test_permission_2(test_permission_1, pg.permission):
            pass
    except pg.FlowException as errors:
        e = errors.get_error('permission-definition-flow',
                             'role-validate-base-classes-node')
        assert str(e) == "Role cant have <class 'pg_definition.objects.permission.permission'> as a base class"

    try:
        class test_permission_1(pg.permission):
            pass

        class test_permission_2(test_permission_1, str):
            pass
    except pg.FlowException as errors:
        e = errors.get_error('permission-definition-flow',
                             'role-validate-base-classes-node')
        assert str(e) == f"Base class {str} must be a permission subclass"

    try:
        class test_permission_1(pg.permission):
            pass

        class test_permission_2(str, test_permission_1):
            pass
    except pg.FlowException as errors:
        e = errors.get_error('permission-definition-flow',
                             'role-validate-base-classes-node')
        assert str(e) == f"Base class {str} must be a permission subclass"

    try:
        class test_permission_1(pg.permission):
            pass

        class test_permission_2(test_permission_1):
            pass

        class test_permission_3(test_permission_2):
            pass
    except pg.FlowException as errors:
        e = errors.get_error('permission-definition-flow',
                             'role-validate-base-classes-node')
        assert str(e) == f"Base class <class 'test_permission_definition.test_role_definition_flow_detects_invalid_bases.<locals>.test_permission_2'> must be a permission, not a role"


def test_permission_definition_flow_extracts_definition_correctly() -> None:
    class test_permission_3(pg.permission):
        pass

    definition: dict[str, Any] = test_permission_3._postgres_definition
    assert definition['type'] == test_permission_3
    assert definition['comment'] is None
    assert definition['type_grants'] == {}
    assert definition['kind'] == 'permission'


def test_role_definition_flow_extracts_definition_correctly() -> None:
    class test_permission_1(pg.permission):
        pass

    class test_permission_2(pg.permission):
        pass

    class test_permission_3(pg.permission):
        pass

    class test_role(test_permission_1, test_permission_2, test_permission_3):
        pass

    definition: dict[str, Any] = test_role._postgres_definition
    assert definition['type'] == test_role
    assert definition['kind'] == 'role'
    assert definition['comment'] is None
    assert definition['permissions'] == (test_permission_1, test_permission_2, test_permission_3, )


def test_grants_correctly_applied_on_permission() -> None:
    def test_grant(grant: dict[str, Any], name: str, tp: type):
        assert name in grant[tp]['grants']

    commenter_def: dict[str, Any] = test_app.roles.commenter._postgres_definition
    consult_perm_def: dict[str, Any] = commenter_def['permissions'][0]._postgres_definition
    test_grant(consult_perm_def['type_grants'], 'references', test_app.test_app.comment)
    test_grant(consult_perm_def['type_grants'], 'select', test_app.test_app.comment)
    create_perm_def: dict[str, Any] = commenter_def['permissions'][1]._postgres_definition
    # test_grant(create_perm_def['type_grants'], 'execute', test_app.test.create_comment)
    test_grant(create_perm_def['type_grants'], 'update', test_app.test_app.comment_id_sequence)
    test_grant(create_perm_def['type_grants'], 'usage', test_app.test_app.comment_id_sequence)
    test_grant(create_perm_def['type_grants'], 'insert', test_app.test_app.comment)
