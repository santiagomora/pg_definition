import pg_definition as pg
from typing_extensions import\
    Annotated
from typing import\
    Optional
import test_app.backend.types as tat
import test_app.backend.cpp.wrapper as tw
# TODO: test that pg.checks are not inherited and neither do pg.comments when defining a domains domain


def test_composite_definition_is_correctly_formed() -> None:
    assert hasattr(tat.composite_author, '__pg_definition')
    definition: dict[str, str] = getattr(tat.composite_author, '__pg_definition')()
    assert 'attributes' in definition
    assert len(definition['attributes']) == 3
    attrs: dict[str, type] = {'id': pg.int8, 'name': pg.text, 'biography': pg.text}
    assert 'comment' in definition
    assert definition['comment'] is None
    for name, attr in definition['attributes'].items():
        assert 'name' in attr
        assert attr['name'] in attrs
        assert 'type' in attr
        assert attr['type'] == attrs[attr['name']]
        assert attr['comment'] is None
        del(attrs[attr['name']])
    assert len(attrs.keys()) == 0
    assert 'type' in definition
    assert definition['type'] == tat.composite_author


def test_composite_flow_detects_non_existing_attribute() -> None:
    try:
        class test(tw.composite_author, metaclass=pg.composite):
            pass
        assert False
    except TypeError:
        pass


def test_composite_flow_validates_single_inheritance() -> None:
    class test1(tw.composite_author, metaclass=pg.composite):
        id: pg.int8
        biography: pg.text
        name: pg.text

    class test2(tw.composite_author, metaclass=pg.composite):
        id: pg.int8
        biography: pg.text
        name: pg.text

    try:
        class test3(test1, test2):
            id: pg.int8
            biography: pg.text
            name: pg.text
        assert False
    except TypeError as e:
        assert str(e) == "compound type <class 'pg_definition.types.composite.composite'> only allows one base class"


def test_composite_flow_detects_invalid_check_in_definition() -> None:
    try:
        class test(tw.composite_author, metaclass=pg.composite):
            id: Annotated[pg.int8, pg.check(
                name='domain_greater_than_0',
                predicate=pg.this() >= pg.literal(0))]
            biography: pg.text
            name: pg.text
        assert False
    except pg.FlowException as e:
        print(e)
        error: Optional[pg.NodeException] = e.get_error('composite-definition-flow',
                                                         'composite-validate-restricted-metadata-types-node')
        assert error is not None
        assert str(error) == f'Invalid metadata type {pg.check} in id declaration'


def test_composite_flow_detects_invalid_attribute_type() -> None:
    try:
        class test(tw.composite_author, metaclass=pg.composite):
            id: Annotated[int, pg.comment('test comment')]
            biography: str
            name: float
    except TypeError:
        pass


def test_composite_flow_extracts_attribute_comment() -> None:
    @pg.add_comment('test comment')
    class test(tw.composite_author, metaclass=pg.composite):
        id: Annotated[pg.int8, pg.comment('test comment')]
        biography: pg.text
        name: pg.text
    assert hasattr(test, '__pg_definition')
    definition: dict[str, str] = getattr(test, '__pg_definition')()
    assert 'attributes' in definition
    assert len(definition['attributes'].keys()) == 3
    assert 'comment' in definition['attributes']['id']
    assert definition['attributes']['id']['comment'].value == 'test comment'
    assert 'comment' in definition
    assert definition['comment'].value == 'test comment'


def test_composite_domain_definition_is_correctly_formed() -> None:
    class test(tw.composite_author, metaclass=pg.composite):
        id: pg.int8
        biography: pg.text
        name: pg.text

    class domain1(test):
        id: pg.int8
        biography: pg.text
        name: pg.text

    definition = getattr(domain1, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == test
    assert 'comment' in definition
    assert definition['comment'] is None


def test_composite_domain_definition_flow_doesnt_allow_additional_fields() -> None:
    # field declaration is already forced upon composites, and they must match
    # underlying c++ fields
    try:
        class test(tw.composite_author, metaclass=pg.composite):
            id: pg.int8
            biography: pg.text
            name: pg.text

        class domain1(test):
            id: pg.int8
            biography: pg.text
            name: pg.text
            test: pg.text
    except TypeError:
        pass


def test_composite_domain_definition_flow_doesnt_allow_field_type_change() -> None:
    try:
        class test(tw.composite_author, metaclass=pg.composite):
            id: pg.int8
            biography: pg.text
            name: pg.text

        class domain1(test):
            id: pg.int2
            biography: pg.text
            name: pg.text

        assert False
    except TypeError:
        pass


def test_composite_domain_subclass_check_constraint_correctly_formed() -> None:
    class test(tw.composite_author, metaclass=pg.composite):
        id: pg.int8
        biography: pg.text
        name: pg.text

    class domain1(test):
        id: Annotated[pg.int8, pg.check(
            name='id_greater_than_0',
            predicate=pg.this() >= pg.literal(0))]
        biography: pg.text
        name: pg.text

    assert hasattr(domain1, '__pg_definition')
    definition = domain1.__pg_definition()
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == test
    assert 'comment' in definition
    assert definition['comment'] is None
    assert definition['check'] is not None
    assert str(definition['check']['domain1_id_greater_than_0']) == '((VALUE).id >= 0)'
    assert definition['check']['domain1_id_greater_than_0'].name == 'domain1_id_greater_than_0'


def test_composite_flow_detects_invalid_metadata() -> None:
    try:
        class test(tw.composite_author, metaclass=pg.composite):
            id: pg.int8
            biography: pg.text
            name: pg.text
        class domain0(test):
            id: pg.int8
            biography: Annotated[pg.text, pg.comment('test comment')]
            name: pg.text
        assert False
    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('composite-definition-flow',
                                                         'composite-domain-validate-restricted-metadata-types-node')
        assert error is not None
        assert str(error) == f'Invalid metadata type {pg.comment} in biography declaration'
    try:
        class test(tw.composite_author, metaclass=pg.composite):
            id: pg.int8
            biography: Annotated[pg.text, pg.check(name='test check', predicate=pg.this() > pg.literal(0))]
            name: pg.text
        assert False
    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('composite-definition-flow',
                                                         'composite-validate-restricted-metadata-types-node')
        assert error is not None
        assert str(error) == f"Invalid metadata type {pg.check} in biography declaration"
