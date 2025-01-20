

#include <pybind11/pybind11.h>
#include "test_app/include/types.hpp"
#include "test_app/include/definitions.hpp"
#include "base_types/include/macros/register.hpp"


namespace py = pybind11;


PYBIND11_MODULE(wrapper, m) {
    PY_DATACLASS_REGISTER(TEST_APP_AUTHOR, m);
    PY_DATACLASS_REGISTER(TEST_APP_AUTHORED, m);
    PY_DATACLASS_REGISTER(TEST_APP_WITH_TIMESTAMPS, m);
    PY_ENUM_REGISTER(TEST_APP_POST_STATUS, m);
    PY_DATACLASS_REGISTER(TEST_APP_POST, m);
    PY_DATACLASS_REGISTER(TEST_APP_COMMENT, m);
    PY_DATACLASS_REGISTER(TEST_APP_COMMENT_POST, m);
    PY_DATACLASS_REGISTER(TEST_APP_COMPOSITE_AUTHOR, m);
}

