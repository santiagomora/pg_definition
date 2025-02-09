#ifndef TEST_APP_API_POST
#define TEST_APP_API_POST
#include "core_pg_bindings/execution/environment.hpp"
#include "core_pg_bindings/execution/invokable.hpp"
#include "test_app/typing/types.hpp"
#include "test_app/api/environment.hpp"
#include "test_app/api/author.hpp"


namespace pg = core_pg_bindings;


namespace test_app
{

class get_post_by_id
    : public pg::invokes_db_function<
          pg::single_result_query_functor,
          pg::OptionalResult_<pg::SingleResult_<post>>, const pg::int8&>
{
protected:
    std::shared_ptr<pg::query_configuration> query_config () const override;
};


class get_post_comments
    : public pg::invokes_db_function<
          pg::multi_result_query_functor,
          pg::ContainedResult_<std::vector, comment>, const post&>
{
protected:
    std::shared_ptr<pg::query_configuration> query_config () const override;
public:
    using pg::invokes_db_function<
          pg::multi_result_query_functor,
          pg::ContainedResult_<std::vector, comment>, const post&>::operator();
    std::optional<std::vector<comment>> operator() (const pg::int8&);
};


class create_post
    : public pg::invokes_db_function<
          pg::single_result_query_functor,
          pg::SingleResult_<post>,
          const author&, const pg::text&, const pg::text&>
{
protected:
    std::shared_ptr<pg::query_configuration> query_config () const override;
public:
    using pg::invokes_db_function<
          pg::single_result_query_functor,
          pg::SingleResult_<post>,
          const author&, const pg::text&, const pg::text&>::operator();
    std::optional<post> operator() (const pg::int8&, const pg::text&, const pg::text&);
};


class create_comment
    : public pg::invokes_db_function<
          pg::single_result_query_functor,
          pg::SingleResult_<comment>,
          const author&, const post&, const pg::text&>
{
protected:
    std::shared_ptr<pg::query_configuration> query_config () const override;
public:
    using pg::invokes_db_function<
          pg::single_result_query_functor,
          pg::SingleResult_<comment>,
          const author&, const post&, const pg::text&>::operator();
    std::optional<comment> operator() (const pg::int8&, const pg::int8&, const pg::text&);
};


class as_comment_post
    : public pg::invokes_db_function<
          pg::single_result_query_functor,
          pg::SingleResult_<comment_post>,
          const post&, const comment&, const pg::text&, const author&>
{
protected:
    std::shared_ptr<pg::query_configuration> query_config () const override;
public:
    using pg::invokes_db_function<
          pg::single_result_query_functor,
          pg::SingleResult_<comment_post>,
          const post&, const comment&, const pg::text&, const author&>::operator();
    std::optional<comment_post> operator() (const pg::int8&, const pg::int8&, const pg::text&, const pg::int8&);
};


#define TEST_APP_API_POST_REGISTER_FUNCTORS(m)\
    py::class_<ta::get_post_by_id>(m, "get_post_by_id")\
        .def(py::init<>())\
        .def("__call__", py::overload_cast<const pg::int8&>(&ta::get_post_by_id::operator()));\
    py::class_<ta::get_post_comments>(m, "get_post_comments")\
        .def(py::init<>())\
        .def("__call__", py::overload_cast<const ta::post&>(&ta::get_post_comments::operator()))\
        .def("__call__", py::overload_cast<const pg::int8&>(&ta::get_post_comments::operator()));\
    py::class_<ta::create_post>(m, "create_post")\
        .def(py::init<>())\
        .def("__call__", py::overload_cast<const ta::author&, const pg::text&, const pg::text&>(&ta::create_post::operator()))\
        .def("__call__", py::overload_cast<const pg::int8&, const pg::text&, const pg::text&>(&ta::create_post::operator()));\
    py::class_<ta::create_comment>(m, "create_comment")\
        .def(py::init<>())\
        .def("__call__", py::overload_cast<const ta::author&, const ta::post&, const pg::text&>(&ta::create_comment::operator()))\
        .def("__call__", py::overload_cast<const pg::int8&, const pg::int8&, const pg::text&>(&ta::create_comment::operator()));\
    py::class_<ta::as_comment_post>(m, "as_comment_post")\
        .def(py::init<>())\
        .def("__call__", py::overload_cast<const ta::post&, const ta::comment&, const pg::text&, const ta::author&>(&ta::as_comment_post::operator()))\
        .def("__call__", py::overload_cast<const pg::int8&, const pg::int8&, const pg::text&, const pg::int8&>(&ta::as_comment_post::operator()))

}

#endif
