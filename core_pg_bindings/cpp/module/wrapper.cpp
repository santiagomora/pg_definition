#include <pybind11/pybind11.h>
#include "core_types/typing/compare.hpp"
#include "core_pg_bindings/macros/register.hpp"
#include "core_pg_bindings/typing/definitions.hpp"
#include "core_pg_bindings/typing/types.hpp"


namespace py = pybind11;


// DEBUG clear && g++ -P -E -I/usr/include/boost -I/home/smora/sgs/dev/python/core/include/ -I/home/smora/.pyenv/versions/3.12.0/include/python3.12/ -I./include wrapper.cpp


PYBIND11_MODULE(wrapper, m)
{
    PG_TYPE_DOMAIN_REGISTER(PG_BOOLEAN, m, PG_BOOLEAN_CONSTRUCTORS);
    PG_TYPE_DOMAIN_REGISTER(PG_INT1, m, PG_INT1_CONSTRUCTORS);
    PG_TYPE_DOMAIN_REGISTER(PG_INT2, m, PG_INT2_CONSTRUCTORS);
    PG_TYPE_DOMAIN_REGISTER(PG_INT4, m, PG_INT4_CONSTRUCTORS);
    PG_TYPE_DOMAIN_REGISTER(PG_INT8, m, PG_INT8_CONSTRUCTORS);
    PG_TYPE_DOMAIN_REGISTER(PG_FLOAT4, m, PG_FLOAT4_CONSTRUCTORS);
    PG_TYPE_DOMAIN_REGISTER(PG_FLOAT8, m, PG_FLOAT8_CONSTRUCTORS);
    PG_TYPE_DOMAIN_REGISTER(PG_TIMESTAMPTZ, m, PG_TIMESTAMPTZ_CONSTRUCTORS);
    PG_TYPE_DOMAIN_REGISTER(PG_DATE, m, PG_DATE_CONSTRUCTORS);
    PG_TYPE_DOMAIN_REGISTER(PG_TEXT, m, PG_TEXT_CONSTRUCTORS);
}
