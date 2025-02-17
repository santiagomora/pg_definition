#include <pybind11/pybind11.h>
#include "test_app/backend/functions.hpp"


namespace py = pybind11;
namespace ta = test_app;


PYBIND11_MODULE (wrapper, m)
{
    m.def("get_author_name", &ta::get_author_name);
}

