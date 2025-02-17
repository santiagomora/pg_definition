#include <pybind11/pybind11.h>
#include <pybind11/stl.h> 
#include "core_pg_bindings/macros/register.hpp"
#include "test_app/database/typing/namespace.hpp"
#include "test_app/database/interface/queries.hpp"

// DEBUG clear && g++ -P -E -I/usr/include/boost -I../../../../core_pg_bindings/cpp -I../../../../../python/core/core_types/core_types/cpp  -I./ wrapper.cpp


namespace py = pybind11;


PYBIND11_MODULE (wrapper, m)
{
// NOTE TYPES
PG_TABLE_REGISTER(TEST_APP_DB_AUTHOR, m);
PG_TABLE_REGISTER(TEST_APP_DB_AUTHORED, m);
PG_TABLE_REGISTER(TEST_APP_DB_WITH_TIMESTAMPS, m);
PG_ENUM_REGISTER(TEST_APP_DB_POST_STATUS, m);
PG_TABLE_REGISTER(TEST_APP_DB_POST, m);
PG_TABLE_REGISTER(TEST_APP_DB_COMMENT, m);
PG_COMPOSITE_REGISTER(TEST_APP_DB_COMMENT_POST, m);
PG_COMPOSITE_REGISTER(TEST_APP_DB_COMPOSITE_AUTHOR, m);
// NOTE FUNCTIONS
PG_INVOKABLE_REGISTER(TEST_APP_DB_GET_AUTHOR_POSTS, m);
PG_INVOKABLE_REGISTER(TEST_APP_DB_CREATE_POST, m);
PG_INVOKABLE_REGISTER(TEST_APP_DB_CREATE_COMMENT, m);
PG_INVOKABLE_REGISTER(TEST_APP_DB_GET_POST_COMMENTS, m);
PG_INVOKABLE_REGISTER(TEST_APP_DB_AS_COMMENT_POST, m);
PG_INVOKABLE_REGISTER(TEST_APP_DB_CREATE_AUTHOR, m);
}
