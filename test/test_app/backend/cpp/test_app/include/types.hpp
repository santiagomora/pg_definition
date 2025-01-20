#ifndef TEST_APP_TYPES
#define TEST_APP_TYPES


#include "./definitions.hpp"

// DEBUG clear && g++ -P -E -I/usr/include/boost -I../../../../../base_types/cpp -I./ -I../../../../../../pg_definition/venv/lib/python3.12/site-packages/pybind11/include wrapper.cpp

namespace test_app {

CPP_DATACLASS(TEST_APP_AUTHOR);
CPP_DATACLASS(TEST_APP_AUTHORED);
CPP_DATACLASS(TEST_APP_WITH_TIMESTAMPS);
CPP_ENUM(TEST_APP_POST_STATUS);
CPP_DATACLASS(TEST_APP_POST);
CPP_DATACLASS(TEST_APP_COMMENT);
CPP_DATACLASS(TEST_APP_COMMENT_POST);
CPP_DATACLASS(TEST_APP_COMPOSITE_AUTHOR);

}


#endif
