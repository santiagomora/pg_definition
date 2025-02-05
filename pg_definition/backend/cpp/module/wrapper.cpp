#include <pybind11/pybind11.h>


// #include "base_types/macros/overload.hpp"
#include "pg_definition/macros/register.hpp"
#include "pg_definition/macros/definition.hpp"
#include "pg_definition/types.hpp"


namespace py = pybind11;


// clear && g++ -P -E -I/usr/include/boost -I./base_types/cpp -I./ -I../../../pg_definition/venv/lib/python3.12/site-packages/pybind11/include wrapper.cpp


PYBIND11_MODULE(wrapper, m) {
    PG_PY_DOMAIN_REGISTER_AS_TYPE(PG_BOOLEAN, m, bl, PG_BOOLEAN_CONSTRUCTORS);
    PG_PY_DOMAIN_REGISTER_AS_TYPE(PG_INT1, m, i1, PG_INT1_CONSTRUCTORS);
    PG_PY_DOMAIN_REGISTER_AS_TYPE(PG_INT2, m, i2, PG_INT2_CONSTRUCTORS);
    PG_PY_DOMAIN_REGISTER_AS_TYPE(PG_INT4, m, i4, PG_INT4_CONSTRUCTORS);
    PG_PY_DOMAIN_REGISTER_AS_TYPE(PG_INT8, m, i8, PG_INT8_CONSTRUCTORS);
    PG_PY_DOMAIN_REGISTER_AS_TYPE(PG_FLOAT4, m, f4, PG_FLOAT4_CONSTRUCTORS);
    PG_PY_DOMAIN_REGISTER_AS_TYPE(PG_FLOAT8, m, f8, PG_FLOAT8_CONSTRUCTORS);
    PG_PY_DOMAIN_REGISTER_AS_TYPE(PG_TIMESTAMPTZ, m, dtz, PG_TIMESTAMPTZ_CONSTRUCTORS);
    PG_PY_DOMAIN_REGISTER_AS_TYPE(PG_DATE, m, dt, PG_DATE_CONSTRUCTORS);
    PG_PY_DOMAIN_REGISTER_AS_TYPE(PG_TEXT, m, tx, PG_TEXT_CONSTRUCTORS);
}

