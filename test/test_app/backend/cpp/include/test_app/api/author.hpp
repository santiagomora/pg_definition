#ifndef TEST_APP_API_AUTHOR
#define TEST_APP_API_AUTHOR
#include "core_pg_bindings/execution/environment.hpp"
#include "core_pg_bindings/execution/invokable.hpp"
#include "test_app/typing/types.hpp"
#include "test_app/api/environment.hpp"


namespace pg = core_pg_bindings;


namespace test_app
{

class create_author
    : public pg::invokes_db_function<
          pg::single_result_query_functor,
          pg::SingleResult_<author>>
{
protected:
    std::shared_ptr<pg::query_configuration> query_config () const override;
};


class get_author_by_id
    : public pg::invokes_db_function<
          pg::single_result_query_functor,
          pg::OptionalResult_<pg::SingleResult_<author>>, const pg::int8&>
{
protected:
    std::shared_ptr<pg::query_configuration> query_config () const override;
};


class get_author_posts
    : public pg::invokes_db_function<
          pg::multi_result_query_functor,
          pg::OptionalResult_<pg::ContainedResult_<std::vector, post>>, const author&>
{
protected:
    std::shared_ptr<pg::query_configuration> query_config () const override;
public:
    using pg::invokes_db_function<
          pg::multi_result_query_functor,
          pg::OptionalResult_<pg::ContainedResult_<std::vector, post>>, const author&>::operator();
    std::optional<std::vector<post>> operator() (const pg::int8&);
};


}


#define TEST_APP_API_AUTHOR_REGISTER_FUNCTORS(m)\
    py::class_<ta::create_author>(m, "create_author")\
        .def(py::init<>())\
        .def("__call__", py::overload_cast<>(&ta::create_author::operator()));\
    py::class_<ta::get_author_by_id>(m, "get_author_by_id")\
        .def(py::init<>())\
        .def("__call__", py::overload_cast<const pg::int8&>(&ta::get_author_by_id::operator()));\
    py::class_<ta::get_author_posts>(m, "get_author_posts")\
        .def(py::init<>())\
        .def("__call__", py::overload_cast<const ta::author&>(&ta::get_author_posts::operator()))\
        .def("__call__", py::overload_cast<const pg::int8&>(&ta::get_author_posts::operator()))


#endif
