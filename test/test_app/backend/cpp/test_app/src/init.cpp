#include <pybind11/pybind11.h>

#include "../include/types.hpp"


namespace py = pybind11;


py::object test_app::author::cls = py::cast<py::none>(Py_None);
py::object test_app::authored::cls = py::cast<py::none>(Py_None);
py::object test_app::with_timestamps::cls = py::cast<py::none>(Py_None);
py::object test_app::post::cls = py::cast<py::none>(Py_None);
py::object test_app::comment::cls = py::cast<py::none>(Py_None);
py::object test_app::comment_post::cls = py::cast<py::none>(Py_None);
py::object test_app::composite_author::cls = py::cast<py::none>(Py_None);
// py::object test_app::domain::cls = py::cast<py::none>(Py_None);
