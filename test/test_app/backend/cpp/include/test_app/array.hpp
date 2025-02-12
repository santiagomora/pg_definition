#ifndef TEST_APP_API_ARRAY
#define TEST_APP_API_ARRAY
#include "core_pg_bindings/execution/environment.hpp"
#include "core_pg_bindings/execution/invokable.hpp"
#include "test_app/database/types.hpp"
#include "test_app/environment.hpp"


namespace pg = core_pg_bindings;


namespace test_app
{

class test_array
    : public pg::queries_database_on_transaction<
          pg::fetch_one_functor,
          pg::ContainedResult_<int>>
{
protected:
    std::shared_ptr<pg::query_configuration> query_config () const override;
};


}


#define TEST_APP_API_ARRAY_REGISTER_FUNCTORS(m)\
    py::class_<ta::test_array>(m, "test_array")\
        .def(py::init<>())\
        .def("__call__", py::overload_cast<>(&ta::test_array::operator()))


#endif
