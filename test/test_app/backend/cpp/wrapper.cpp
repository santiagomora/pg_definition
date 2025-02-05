#include "pg_definition/macros/register.hpp"

#include "test_app/types.hpp"


namespace py = pybind11;


// DEBUG clear && g++ -P -E -I/usr/include/boost -I../../../../pg_definition/cpp -I../../../../../base_types/base_types/cpp  -I./ wrapper.cpp


PYBIND11_MODULE (wrapper, m) {

    PG_PY_TABLE_REGISTER(TEST_APP_AUTHOR, m);
    PG_PY_TABLE_REGISTER(TEST_APP_AUTHORED, m);
    PG_PY_TABLE_REGISTER(TEST_APP_WITH_TIMESTAMPS, m);
    PG_PY_ENUM_REGISTER(TEST_APP_POST_STATUS, m);
    PG_PY_TABLE_REGISTER(TEST_APP_POST, m);
    PG_PY_TABLE_REGISTER(TEST_APP_COMMENT, m);
    PG_PY_COMPOSITE_REGISTER(TEST_APP_COMMENT_POST, m);
    PG_PY_COMPOSITE_REGISTER(TEST_APP_COMPOSITE_AUTHOR, m);

    m.def("create_author", &test_app::create_author);
    m.def("get_author_by_id", py::overload_cast<pg::int8&>(&test_app::get_author_by_id));
    m.def("get_author_posts", py::overload_cast<test_app::author&>(&test_app::get_author_posts));
    m.def("get_author_posts", py::overload_cast<pg::int8&>(&test_app::get_author_posts));

    m.def("get_post_by_id", py::overload_cast<pg::int8&>(&test_app::get_post_by_id));
    m.def("get_post_comments", py::overload_cast<pg::int8&>(&test_app::get_post_comments));
    m.def("get_post_comments", py::overload_cast<test_app::post&>(&test_app::get_post_comments));
    m.def("create_post", py::overload_cast<pg::int8&, pg::text&, pg::text&>(&test_app::create_post));
    m.def("create_post", py::overload_cast<test_app::author&, pg::text&, pg::text&>(&test_app::create_post));
    m.def("create_comment", py::overload_cast<pg::int8&, pg::int8&, pg::text&>(&test_app::create_comment));
    m.def("create_comment", py::overload_cast<test_app::author&, test_app::post&, pg::text&>(&test_app::create_comment));
    m.def("as_comment_post", py::overload_cast<pg::int8&, pg::int8&, pg::text&, pg::int8&>(&test_app::as_comment_post));
    m.def("as_comment_post", py::overload_cast<test_app::post&, test_app::comment&, pg::text&, test_app::author&>(&test_app::as_comment_post));

}

