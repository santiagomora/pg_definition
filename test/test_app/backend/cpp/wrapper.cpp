#include "core_pg_bindings/macros/register.hpp"
#include "test_app/typing/types.hpp"
#include "test_app/api/author.hpp"
#include "test_app/api/post.hpp"
// #include "test_app/api/array.hpp"
#include "test_app/api/environment.hpp"


// DEBUG clear && g++ -P -E -I/usr/include/boost -I../../../../core_pg_bindings/cpp -I../../../../../python/core/core_types/core_types/cpp  -I./ wrapper.cpp


namespace py = pybind11;
namespace ta = test_app;
namespace pg = core_pg_bindings;


PYBIND11_MODULE (wrapper, m)
{
    
    PG_PY_TABLE_REGISTER(TEST_APP_AUTHOR, m);
    PG_PY_TABLE_REGISTER(TEST_APP_AUTHORED, m);
    PG_PY_TABLE_REGISTER(TEST_APP_WITH_TIMESTAMPS, m);
    PG_PY_ENUM_REGISTER(TEST_APP_POST_STATUS, m);
    PG_PY_TABLE_REGISTER(TEST_APP_POST, m);
    PG_PY_TABLE_REGISTER(TEST_APP_COMMENT, m);
    PG_PY_COMPOSITE_REGISTER(TEST_APP_COMMENT_POST, m);
    PG_PY_COMPOSITE_REGISTER(TEST_APP_COMPOSITE_AUTHOR, m);
    
    TEST_APP_API_AUTHOR_REGISTER_FUNCTORS(m);
    TEST_APP_API_POST_REGISTER_FUNCTORS(m);
    // TEST_APP_API_ARRAY_REGISTER_FUNCTORS(m);
}

