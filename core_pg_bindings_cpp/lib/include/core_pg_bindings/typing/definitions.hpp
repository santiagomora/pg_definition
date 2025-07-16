#ifndef CORE_PG_BINDINGS_TYPING_DEFINITIONS
#define CORE_PG_BINDINGS_TYPING_DEFINITIONS
#include "core_types/typing/definitions.hpp"
#include "core_pg_bindings/macros/definition.hpp"


#define PG_BOOLEAN PG_TYPE_DOMAIN_DEFINITION(\
    PG_BOOLEAN,\
    (core_pg_bindings, boolean),\
    CT_BOOLEAN,\
    (core_pg_bindings::interface, boolean)\
)
#define PG_BOOLEAN_CONSTRUCTORS (PG_BOOLEAN) CT_BOOLEAN_CONSTRUCTORS
#define PG_BOOLEAN_INHERITANCE_CHAIN (CT_BOOLEAN)


// TYPE ALIAS
#define PG_INT1 PG_TYPE_DOMAIN_DEFINITION(\
    PG_INT1,\
    (core_pg_bindings, int1),\
    CT_INT1,\
    (core_pg_bindings::interface, int1)\
)
#define PG_INT1_CONSTRUCTORS (PG_INT1) CT_INT1_CONSTRUCTORS
#define PG_INT1_INHERITANCE_CHAIN (CT_INT1)


#define PG_INT2 PG_TYPE_DOMAIN_DEFINITION(\
    PG_INT2,\
    (core_pg_bindings, int2),\
    CT_INT2,\
    (core_pg_bindings::interface, int2)\
)
#define PG_INT2_CONSTRUCTORS (PG_INT2) CT_INT2_CONSTRUCTORS
#define PG_INT2_INHERITANCE_CHAIN (CT_INT2)


#define PG_INT4 PG_TYPE_DOMAIN_DEFINITION(\
    PG_INT4,\
    (core_pg_bindings, int4),\
    CT_INT4,\
    (core_pg_bindings::interface, int4)\
)
#define PG_INT4_CONSTRUCTORS (PG_INT4) CT_INT4_CONSTRUCTORS
#define PG_INT4_INHERITANCE_CHAIN (CT_INT4)


#define PG_INT8 PG_TYPE_DOMAIN_DEFINITION(\
    PG_INT8,\
    (core_pg_bindings, int8),\
    CT_INT8,\
    (core_pg_bindings::interface, int8)\
)
#define PG_INT8_CONSTRUCTORS (PG_INT8) CT_INT8_CONSTRUCTORS
#define PG_INT8_INHERITANCE_CHAIN (CT_INT8)


#define PG_FLOAT4 PG_TYPE_DOMAIN_DEFINITION(\
    PG_FLOAT4,\
    (core_pg_bindings, float4),\
    CT_FLOAT4,\
    (core_pg_bindings::interface, float4)\
)
#define PG_FLOAT4_CONSTRUCTORS (PG_FLOAT4) CT_FLOAT4_CONSTRUCTORS
#define PG_FLOAT4_INHERITANCE_CHAIN (CT_FLOAT4)


#define PG_FLOAT8 PG_TYPE_DOMAIN_DEFINITION(\
    PG_FLOAT8,\
    (core_pg_bindings, float8),\
    CT_FLOAT8,\
    (core_pg_bindings::interface, float8)\
)
#define PG_FLOAT8_CONSTRUCTORS (PG_FLOAT8) CT_FLOAT8_CONSTRUCTORS
#define PG_FLOAT8_INHERITANCE_CHAIN (CT_FLOAT8)


#define PG_TEXT PG_TYPE_DOMAIN_DEFINITION(\
    PG_TEXT,\
    (core_pg_bindings, text),\
    CT_TEXT,\
    (core_pg_bindings::interface, text)\
)
#define PG_TEXT_CONSTRUCTORS (PG_TEXT) CT_TEXT_CONSTRUCTORS
#define PG_TEXT_INHERITANCE_CHAIN (CT_TEXT)


#define PG_TIMESTAMPTZ PG_TYPE_DOMAIN_DEFINITION(\
    PG_TIMESTAMPTZ,\
    (core_pg_bindings, timestamptz),\
    CT_TIMESTAMPTZ,\
    (core_pg_bindings::interface, timestamptz)\
)
#define PG_TIMESTAMPTZ_CONSTRUCTORS (PG_TIMESTAMPTZ) CT_TIMESTAMPTZ_CONSTRUCTORS
#define PG_TIMESTAMPTZ_INHERITANCE_CHAIN (CT_TIMESTAMPTZ)


#define PG_DATE PG_TYPE_DOMAIN_DEFINITION(\
    PG_DATE,\
    (core_pg_bindings, date),\
    CT_DATE,\
    (core_pg_bindings::interface, date)\
)
#define PG_DATE_CONSTRUCTORS (PG_DATE) CT_DATE_CONSTRUCTORS
#define PG_DATE_INHERITANCE_CHAIN (CT_DATE)


#endif
