#include <pybind11/pybind11.h>


// #include "core_types/macros/overload.hpp"
#include "core_pg_bindings/macros/register.hpp"
#include "core_pg_bindings/macros/definition.hpp"
#include "core_pg_bindings/typing/definitions.hpp"
#include "core_pg_bindings/typing/types.hpp"


namespace py = pybind11;


// clear && g++ -P -E -I/usr/include/boost -I./core_types/cpp -I./ -I../../../core_pg_bindings/venv/lib/python3.12/site-packages/pybind11/include wrapper.cpp


PYBIND11_MODULE(wrapper, m) {
    PG_PY_REGISTER_TYPE_DOMAIN(PG_BOOLEAN, m, bl, PG_BOOLEAN_CONSTRUCTORS);
    PG_PY_REGISTER_TYPE_DOMAIN(PG_INT1, m, i1, PG_INT1_CONSTRUCTORS);
    PG_PY_REGISTER_TYPE_DOMAIN(PG_INT2, m, i2, PG_INT2_CONSTRUCTORS);
    PG_PY_REGISTER_TYPE_DOMAIN(PG_INT4, m, i4, PG_INT4_CONSTRUCTORS);
    PG_PY_REGISTER_TYPE_DOMAIN(PG_INT8, m, i8, PG_INT8_CONSTRUCTORS);
    PG_PY_REGISTER_TYPE_DOMAIN(PG_FLOAT4, m, f4, PG_FLOAT4_CONSTRUCTORS);
    PG_PY_REGISTER_TYPE_DOMAIN(PG_FLOAT8, m, f8, PG_FLOAT8_CONSTRUCTORS);
    PG_PY_REGISTER_TYPE_DOMAIN(PG_TIMESTAMPTZ, m, dtz, PG_TIMESTAMPTZ_CONSTRUCTORS);
    PG_PY_REGISTER_TYPE_DOMAIN(PG_DATE, m, dt, PG_DATE_CONSTRUCTORS);
    PG_PY_REGISTER_TYPE_DOMAIN(PG_TEXT, m, tx, PG_TEXT_CONSTRUCTORS);
}

