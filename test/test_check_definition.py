from pgdriver.definition.base.common.meta import\
    literal,\
    this,\
    field,\
    length
from typing import\
    Any


def test_check_arithmetic_predicates_and_values() -> None:
    def test_operation(op: Any, op_str: str) -> None:
        print(op_str)
        assert str(op) == op_str
        assert eval(str(op)) == eval(op_str)
        assert op.value(None, None) == eval(op_str)
    test_operation(literal(3) + literal(5) + literal(6), '3 + 5 + 6')
    test_operation(literal(3) - (literal(5) + literal(6)), '3 - (5 + 6)')
    test_operation((literal(3) + literal(3)) + (literal(5) + literal(6)), '3 + 3 + 5 + 6')
    test_operation((literal(3) + literal(3))*literal(5), '(3 + 3) * 5')
    test_operation(literal(5) * (literal(3) + literal(3)), '5 * (3 + 3)')
    test_operation(literal(5) * (literal(3) + literal(3)) * literal(4), '5 * (3 + 3) * 4')
    test_operation(literal(5) * (literal(2) - (literal(3) + literal(3))) * literal(4), '5 * (2 - (3 + 3)) * 4')
    test_operation((literal(3) - (literal(5) + literal(6) - (literal(5) + literal(6))))*literal(4), '(3 - (5 + 6 - (5 + 6))) * 4')
    test_operation(literal(3) - (literal(5) + literal(6) - (literal(5) + literal(6)))*literal(4), '3 - (5 + 6 - (5 + 6)) * 4')
    test_operation((literal(3) - (literal(5) + literal(6) - (literal(5) + literal(6))))/literal(4), '(3 - (5 + 6 - (5 + 6))) / 4')
    test_operation(literal(3) - (literal(5) + literal(6) - (literal(5) + literal(6)))/literal(4), '3 - ((5 + 6 - (5 + 6)) / 4)')
    test_operation((literal(5) + literal(6)) / (literal(4) - (literal(5) + literal(6)))*literal(4), '((5 + 6) / (4 - (5 + 6))) * 4')
    test_operation(literal(5) / ((literal(4) - (literal(5) + literal(6)))*literal(4)), '5 / ((4 - (5 + 6)) * 4)')
    test_operation((literal(4) - (literal(5) + literal(6)))*(literal(5) + literal(4)), '(4 - (5 + 6)) * (5 + 4)')
    test_operation(literal(4)/literal(5) + literal(6) + literal(5)/literal(4), '(4 / 5) + 6 + (5 / 4)')
    test_operation(literal(4)/literal(5) + literal(6) + literal(5)/literal(4), '(4 / 5) + 6 + (5 / 4)')
    test_operation((literal(4)/literal(5) + literal(6) + literal(5))/literal(4), '((4 / 5) + 6 + 5) / 4')
    test_operation(literal(4)/(literal(5) * literal(6) * literal(5)), '4 / (5 * 6 * 5)')
    test_operation(literal(4)/literal(5) * literal(6) * literal(5), '(4 / 5) * 6 * 5')
    test_operation(literal(4) * literal(3) * literal(2)/(literal(5) * literal(6) * literal(5)), '4 * 3 * 2 / (5 * 6 * 5)')
    test_operation(literal(4) * literal(3) * literal(2)/(literal(5) * literal(6)) * literal(5), '(4 * 3 * 2 / (5 * 6)) * 5')
    test_operation((literal(4) + literal(3) * literal(2))/(literal(5) * literal(6)) + literal(5), '((4 + 3 * 2) / (5 * 6)) + 5')
    test_operation((literal(4) + literal(3) * literal(2))/((literal(5) * literal(6)) + literal(5)) / literal(6), '((4 + 3 * 2) / (5 * 6 + 5)) / 6')
    test_operation((literal(6)/(literal(4) + literal(3) * literal(2)))/((literal(5) * literal(6)) + literal(5)), '(6 / (4 + 3 * 2)) / (5 * 6 + 5)')
    test_operation((literal(6)/(literal(4) + literal(3) * literal(2)))/((literal(5) * literal(6)) + literal(5)), '(6 / (4 + 3 * 2)) / (5 * 6 + 5)')
    test_operation(literal(6)/((literal(4) + literal(3) * literal(2))/((literal(5) * literal(6)) + literal(5))), '6 / ((4 + 3 * 2) / (5 * 6 + 5))')
    test_operation(literal(6) / (literal(2) / (literal(5) / literal(6))), '6 / (2 / (5 / 6))')
    test_operation((literal(6) / literal(2)) / (literal(5) / literal(6)), '(6 / 2) / (5 / 6)')
    test_operation((literal(6) / literal(2) / literal(5)) / literal(6), '((6 / 2) / 5) / 6')
    test_operation(literal(6) / ((literal(2) / literal(5)) / literal(6)), '6 / ((2 / 5) / 6)')
    test_operation((literal(6) / (literal(2) / literal(5))) / literal(6), '(6 / (2 / 5)) / 6')
    test_operation(literal(5) / ((literal(3) + literal(2)) * literal(6)), '5 / ((3 + 2) * 6)')
    test_operation(literal(5) / (literal(3) + literal(2)) * literal(6), '(5 / (3 + 2)) * 6')
    test_operation(literal(1) * literal(2) * literal(3) / literal(5) * literal(4) * literal(5), '(1 * 2 * 3 / 5) * 4 * 5')
    test_operation(literal(1) * literal(2) * (literal(3) / literal(5)) * literal(4) * literal(5), '1 * 2 * (3 / 5) * 4 * 5')
    test_operation(literal(1) * literal(2) * (literal(3) / literal(5)) * literal(4) * literal(5), '1 * 2 * (3 / 5) * 4 * 5')
    test_operation(literal(1) * (literal(2) * literal(3) / literal(5)) * literal(4) * literal(5), '1 * (2 * 3 / 5) * 4 * 5')
    test_operation(literal(1) * ((literal(2) + literal(3)) / literal(5)) * literal(4) * literal(5), '1 * ((2 + 3) / 5) * 4 * 5')
    test_operation(((literal(1) *(literal(2) + literal(3))) / (literal(5) * literal(4))) * literal(5), '(1 * (2 + 3) / (5 * 4)) * 5')
    test_operation(literal(1) * ((literal(2) + literal(3)) / (literal(5) * literal(4))) * literal(5), '1 * ((2 + 3) / (5 * 4)) * 5')
    test_operation(((literal(2) + literal(3)) / (literal(5) * literal(4))) * literal(5), '((2 + 3) / (5 * 4)) * 5')


def test_check_logic_predicates_and_values() -> None:
    # even though python supports three operand comparison postgres doesnt.
    # I couldnt find a way to prevent user from creating them with the current API.
    # So be warned.
    def test_operation(op: Any, op_str: str) -> None:
        print(op_str)
        assert str(op) == op_str
        assert eval(str(op).lower()) == eval(op_str.lower())
        assert op.value(None, None) == eval(op_str.lower())
    test_operation((literal(5) > literal(4)) & (literal(1) > literal(2)), '(5 > 4) AND (1 > 2)')
    test_operation((literal(1) * ((literal(2) + literal(3)) / (literal(5) * literal(4))) * literal(5)) > (((literal(2) + literal(3)) / (literal(5) * literal(4))) * literal(5)), '(1 * ((2 + 3) / (5 * 4)) * 5) > (((2 + 3) / (5 * 4)) * 5)')
    test_operation((literal(5) > literal(2)) | (literal(3) > literal(4)) | (literal(1) > literal(2)), '(5 > 2) OR (3 > 4) OR (1 > 2)')
    test_operation(((literal(5) > literal(2)) | (literal(5) > literal(2))) | (literal(5) > literal(2)) | (literal(3) > literal(4)), '(5 > 2) OR (5 > 2) OR (5 > 2) OR (3 > 4)')
    test_operation((((literal(5) > literal(2)) | (literal(5) > literal(2))) | (literal(5) > literal(2))) | (literal(3) > literal(4)), '(5 > 2) OR (5 > 2) OR (5 > 2) OR (3 > 4)')
    test_operation((((literal(5) > literal(2)) | (literal(5) > literal(2)) | (literal(5) > literal(2)))) | (literal(3) > literal(4)), '(5 > 2) OR (5 > 2) OR (5 > 2) OR (3 > 4)')
    test_operation((literal(5) > literal(2)) | ((literal(5) > literal(2)) | (literal(5) > literal(2))) | (literal(3) > literal(4)), '(5 > 2) OR ((5 > 2) OR (5 > 2)) OR (3 > 4)')
    test_operation((literal(5) > literal(2)) | ((literal(5) > literal(2)) | ((literal(5) > literal(2))) | (literal(3) > literal(4))), '(5 > 2) OR ((5 > 2) OR (5 > 2) OR (3 > 4))')
    test_operation((literal(5) > literal(2)) | ((literal(5) > literal(2)) | (literal(5) > literal(2)) | (literal(3) > literal(4))), '(5 > 2) OR ((5 > 2) OR (5 > 2) OR (3 > 4))')
    test_operation((literal(5) > literal(2)) | ((literal(5) > literal(2)) | ((literal(5) > literal(2)) | (literal(3) > literal(4)))), '(5 > 2) OR ((5 > 2) OR ((5 > 2) OR (3 > 4)))')
    test_operation(((literal(5) > literal(2)) & (literal(5) > literal(2))) & (literal(5) > literal(2)) & (literal(3) > literal(4)), '(5 > 2) AND (5 > 2) AND (5 > 2) AND (3 > 4)')
    test_operation((((literal(5) > literal(2)) & (literal(5) > literal(2))) & (literal(5) > literal(2))) & (literal(3) > literal(4)), '(5 > 2) AND (5 > 2) AND (5 > 2) AND (3 > 4)')
    test_operation((((literal(5) > literal(2)) & (literal(5) > literal(2)) & (literal(5) > literal(2)))) & (literal(3) > literal(4)), '(5 > 2) AND (5 > 2) AND (5 > 2) AND (3 > 4)')
    test_operation((literal(5) > literal(2)) & ((literal(5) > literal(2)) & (literal(5) > literal(2))) & (literal(3) > literal(4)), '(5 > 2) AND ((5 > 2) AND (5 > 2)) AND (3 > 4)')
    test_operation((literal(5) > literal(2)) & ((literal(5) > literal(2)) & ((literal(5) > literal(2))) & (literal(3) > literal(4))), '(5 > 2) AND ((5 > 2) AND (5 > 2) AND (3 > 4))')
    test_operation((literal(5) > literal(2)) & ((literal(5) > literal(2)) & (literal(5) > literal(2)) & (literal(3) > literal(4))), '(5 > 2) AND ((5 > 2) AND (5 > 2) AND (3 > 4))')
    test_operation((literal(5) > literal(2)) & ((literal(5) > literal(2)) & ((literal(5) > literal(2)) & (literal(3) > literal(4)))), '(5 > 2) AND ((5 > 2) AND ((5 > 2) AND (3 > 4)))')
    test_operation((literal(5) > literal(2)) | (literal(5) > literal(2)) & (literal(3) > literal(4)), '(5 > 2) OR ((5 > 2) AND (3 > 4))')
    test_operation(((literal(5) > literal(2)) | (literal(5) > literal(2))) & (literal(3) > literal(4)), '((5 > 2) OR (5 > 2)) AND (3 > 4)')
    test_operation(((literal(5) == literal(2)) | (literal(3) >= literal(4))) | (literal(1) < literal(2)), '(5 == 2) OR (3 >= 4) OR (1 < 2)')
    test_operation(((literal(5) != literal(2)) & (literal(3) >= literal(4))) | (literal(1) <= literal(2)), '((5 != 2) AND (3 >= 4)) OR (1 <= 2)')
    test_operation((literal(5) < literal(2)) & ((literal(3) == literal(4)) | (literal(1) != literal(2))), '(5 < 2) AND ((3 == 4) OR (1 != 2))')
