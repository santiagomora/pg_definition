from pgdriver import\
    smallint,\
    text,\
    composite,\
    timestamptz,\
    timetz,\
    date,\
    with_comment,\
    comment,\
    check,\
    with_default_value,\
    with_check,\
    default_value,\
    FlowException,\
    NodeException,\
    literal,\
    field,\
    this,\
    builtin
from typing_extensions import\
    Annotated
from typing import\
    Optional
import pydantic_core
import datetime


# TODO: test that checks are not inherited and neither do comments when defining a domains domain


def test_composite_definition_is_correctly_formed() -> None:
    class test(composite):
        field_1: smallint
        field_2: text

    assert hasattr(test, '__pg_definition')
    definition: dict[str, str] = getattr(test, '__pg_definition')()
    assert 'attributes' in definition
    assert len(definition['attributes']) == 2
    attrs: dict[str, type] = {'field_1': smallint, 'field_2': text}
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
    assert definition['type'] == test


def test_composite_flow_detects_non_existing_attribute() -> None:
    try:
        class test(composite):
            pass
    except FlowException as e:
        error: Optional[NodeException] = e.get_error('composite-definition-flow',
                                                         'composite-extract-attributes-node')
        assert error is not None
        assert str(error) == "Class <class 'test_composite_definition.\
test_composite_flow_detects_non_existing_attribute.<locals>.test'> must \
declare attributes."


def test_composite_flow_validates_single_inheritance() -> None:
    class test1(composite):
        field_1: smallint

    class test2(composite):
        field_2: text

    try:
        class test3(test1, test2):
            pass
    except TypeError as e:
        assert str(e) == "Class <class 'pgdriver.definition.common.model._PGBaseModelMeta'> doesnt allow multiple bases"


def test_composite_flow_detects_invalid_check_in_definition() -> None:
    try:
        class test(composite):
            field_1: Annotated[smallint,
                               check(name='domain_greater_than_0',
                                        predicate=this() >= literal(0))]
    except FlowException as e:
        error: Optional[NodeException] = e.get_error('composite-definition-flow',
                                                         'composite-validate-restricted-metadata-types-node')
        assert error is not None
        assert str(error) == f'Invalid metadata type {check} in field_1 declaration'


def test_composite_flow_detects_invalid_attribute_type() -> None:
    try:
        class test(composite):
            field_1: int
            field_2: str
            field_3: float
            field_4: bytes
            field_5: datetime.datetime
            field_6: datetime.time
            field_7: datetime.date
            field_8: bool
    except FlowException as e:
        error: Optional[NodeException] = e.get_error('composite-definition-flow',
                                                         'composite-validate-fields-base-type-node')
        assert error is not None
        field_errors: list[str] = [
            f'Field field_3 type must be a subclass of {builtin}',
            f'Field field_2 type must be a subclass of {builtin}',
            f'Field field_6 type must be a subclass of {builtin}',
            f'Field field_7 type must be a subclass of {builtin}',
            f'Field field_5 type must be a subclass of {builtin}',
            f'Field field_4 type must be a subclass of {builtin}',
            f'Field field_1 type must be a subclass of {builtin}',
            f'Field field_8 type must be a subclass of {builtin}']
        for err in field_errors:
            assert err in error.error_list


def test_composite_flow_extracts_attribute_comment() -> None:
    class test(composite):
        field_1: Annotated[smallint,
                           comment('test comment')]
    assert hasattr(test, '__pg_definition')
    definition: dict[str, str] = getattr(test, '__pg_definition')()
    assert 'attributes' in definition
    assert len(definition['attributes'].keys()) == 1
    assert 'comment' in definition['attributes']['field_1']
    assert definition['attributes']['field_1']['comment'].value == 'test comment'


def test_composite_flow_extracts_comment() -> None:
    @with_comment('test comment')
    class test(composite):
        field_1: smallint
    assert hasattr(test, '__pg_definition')
    definition: dict[str, str] = getattr(test, '__pg_definition')()
    assert 'comment' in definition
    assert definition['comment'].value == 'test comment'


def test_composite_domain_definition_is_correctly_formed() -> None:
    class test(composite):
        field_1: smallint

    class domain1(test):
        pass

    definition = getattr(domain1, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == test
    assert 'comment' in definition
    assert definition['comment'] is None


def test_composite_domain_definition_flow_doesnt_allow_additional_fields() -> None:
    try:
        class test(composite):
            field_1: smallint

        class domain1(test):
            field_2: text
    except FlowException as e:
        error: Optional[NodeException] = e.get_error('composite-definition-flow',
                                                         'composite-domain-validate-declared-attributes-node')
        assert error is not None
        assert str(error) == 'Additional attribute field_2 detected in composite domain definition'


def test_composite_domain_definition_flow_doesnt_allow_field_type_change() -> None:
    try:
        class test(composite):
            field_1: smallint

        class domain1(test):
            field_1: text

        assert False
    except FlowException as e:
        error: Optional[NodeException] = e.get_error('composite-definition-flow',
                                                         'composite-domain-validate-declared-attributes-node')
        assert error is not None
        assert str(error) == f'Composite domain attribute type must match type in parent definition. Expected {text} to be {smallint}'


def test_composite_domain_subclass_check_constraint_correctly_formed() -> None:
    class test(composite):
        field_1: smallint

    class domain1(test):
        field_1: Annotated[smallint,
                           check(name='field1_greater_than_0',
                                    predicate=this() >= literal(0))]

    assert hasattr(domain1, '__pg_definition')
    definition = domain1.__pg_definition()
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == test
    assert 'comment' in definition
    assert definition['comment'] is None
    assert definition['check'] is not None
    assert str(definition['check']['domain1_field1_greater_than_0']) == '((VALUE).field_1 >= 0)'
    assert definition['check']['domain1_field1_greater_than_0'].name == 'domain1_field1_greater_than_0'


def test_composite_domain_subclass_merges_check_constraints() -> None:
    class test(composite):
        field_1: smallint

    class domain1(test):
        field_1: Annotated[smallint,
                           check(name='field1_greater_than_0',
                                    predicate=this() >= literal(0))]

    class domain2(domain1):
        field_1: Annotated[smallint,
                           check(name='field1_less_than_10',
                                    predicate=this() <= literal(10))]

    class domain3(domain2):
        pass

    try:
        domain2(field_1=11)
        assert False
    except pydantic_core._pydantic_core.ValidationError as e:
        assert str(e) == '1 validation error for domain2\n\
field_1\n\
  Value error, domain2_field1_less_than_10: constraint validation failed for value "11" [type=value_error, input_value=11, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'
    try:
        domain2(field_1=-1)
        assert False
    except pydantic_core._pydantic_core.ValidationError as e:
        assert str(e) == '1 validation error for domain1\n\
field_1\n\
  Value error, domain1_field1_greater_than_0: constraint validation failed for value "-1" [type=value_error, input_value=-1, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'
    d2_instance = domain2(field_1=2)
    assert d2_instance.field_1 == 2
    try:
        domain3(field_1=-1)
        assert False
    except pydantic_core._pydantic_core.ValidationError as e:
        assert str(e) == '1 validation error for domain1\n\
field_1\n\
  Value error, domain1_field1_greater_than_0: constraint validation failed for value "-1" [type=value_error, input_value=-1, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'
    try:
        domain3(field_1=11)
        assert False
    except pydantic_core._pydantic_core.ValidationError as e:
        assert str(e) == '1 validation error for domain2\n\
field_1\n\
  Value error, domain2_field1_less_than_10: constraint validation failed for value "11" [type=value_error, input_value=11, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'


def test_composite_domain_subclass_doesnt_inherit_comments() -> None:
    try:
        class test(composite):
            field_1: Annotated[smallint,
                               comment('test')]

        class domain1(test):
            pass
        assert True
    except FlowException as e:
        error: Optional[NodeException] = e.get_error('composite-definition-flow',
                                                         'composite-domain-validate-restricted-metadata-types-node')
        assert error is not None
        if str(error) == "Invalid metadata type <class 'pgdriver.definition.definition.meta.comment'> in field_1 declaration":
            assert False

    @with_comment('test comment')
    class test2(composite):
        field_1: Annotated[smallint,
                           comment('test')]

    class domain2(test2):
        pass

    definition = getattr(domain2, '__pg_definition')()
    assert 'comment' in definition
    assert definition['comment'] is None


def test_composite_flow_detects_invalid_metadata() -> None:
    try:
        class test(composite):
            field_1: smallint

        class domain1(test):
            field_1: Annotated[smallint,
                               comment('test')]
    except FlowException as e:
        error: Optional[NodeException] = e.get_error('composite-definition-flow',
                                                         'composite-domain-validate-restricted-metadata-types-node')
        assert error is not None
        assert str(error) == f'Invalid metadata type {comment} in field_1 declaration'
    try:
        # class test2(composite):
            field_1: Annotated[smallint,
                               check(name='field1_greater_than_0',
                                        predicate=this() >= literal(0))]

    except FlowException as e:
        error: Optional[NodeException] = e.get_error('composite-definition-flow',
                                                         'composite-validate-restricted-metadata-types-node')
        assert error is not None
        assert str(error) == "Invalid metadata type <class 'pgdriver.definition.definition.meta.check'> in field_1 declaration"


def test_composite_support_complex_type_creation() -> None:
    class domain0(smallint):
        pass

    @with_default_value(2)
    class domain1(domain0):
        pass

    assert hasattr(domain1, '__pg_definition')
    definition: dict[str, str] = getattr(domain1, '__pg_definition')()
    assert 'default_value' in definition
    assert definition['default_value'] is not None
    assert isinstance(definition['default_value'], default_value)
    assert isinstance(definition['default_value'].default, literal)
    assert isinstance(definition['default_value'].default._lit, domain1)
    assert definition['default_value'].default._lit == 2

    class test1(composite):
        f1: smallint
        f2: timestamptz
        f3: timetz
        f4: date

    class test2(composite):
        f1: test1
        f2: smallint

    d = test2(f1={'f1': 1, 'f2': '2020-10-11', 'f3': '10:20:01', 'f4': '2020-11-11'}, f2=1)
    assert isinstance(d.f1.f1, smallint)
    assert isinstance(d.f1.f2, timestamptz)
    assert isinstance(d.f1.f3, timetz)
    assert isinstance(d.f1.f4, date)
    assert isinstance(d.f2, smallint)

    @with_check(name='constrained_datetime_check', predicate=this() > literal('2020-10-10'))
    class constrained_datetime(timestamptz):
        pass

    class constrained_date(date):
        pass

    class test3(composite):
        f1: smallint
        f2: constrained_datetime
        f3: timetz
        f4: constrained_date

    class test4(composite):
        f1: test3
        f2: smallint

    d = test4(f1={'f1': 1, 'f2': '2020-10-11', 'f3': '10:20:01', 'f4': '2020-11-11'}, f2=1)
    assert isinstance(d.f1.f1, smallint)
    assert isinstance(d.f1.f2, constrained_datetime)
    assert isinstance(d.f1.f3, timetz)
    assert isinstance(d.f1.f4, constrained_date)
    assert isinstance(d.f2, smallint)

    try:
        d = test4(f1={'f1': 1, 'f2': '2020-10-09', 'f3': '10:20:01', 'f4': '2020-11-11'}, f2=1)
    except pydantic_core._pydantic_core.ValidationError as e:
        print(str(e))
        assert str(e) == '1 validation error for test4\n\
f1.f2\n\
  Value error, constrained_datetime_check: constraint validation failed for value "2020-10-09 00:00:00" [type=value_error, input_value=\'2020-10-09\', input_type=str]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'


def test_composite_misc_check_tests() -> None:
    class test(composite):
        f1: smallint
        f2: smallint

    class domain(test):
        f2: Annotated[smallint, check(name='f2_gt_f1', predicate=this() > field('f1'))]

    try:
        domain(f1=2, f2=1)
        assert False
    except pydantic_core._pydantic_core.ValidationError as e:
        assert str(e) == '1 validation error for domain\n\
f2\n\
  Value error, domain_f2_gt_f1: constraint validation failed for value "1" [type=value_error, input_value=1, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'
