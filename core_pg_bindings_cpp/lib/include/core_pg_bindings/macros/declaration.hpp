#ifndef CORE_PG_BINDINGS_MACROS_DECLARATION
#define CORE_PG_BINDINGS_MACROS_DECLARATION
#include "core_types/macros/backend.hpp"
#include "core_types/macros/interface.hpp"
#include "core_pg_bindings/macros/definition.hpp"


// NOTE DECLARATIONS
#define PG_CPP_TABLE_DECLARATION     CPP_CLASSDEF_DECLARATION
#define PG_CPP_COMPOSITE_DECLARATION CPP_CLASSDEF_DECLARATION
#define PG_CPP_ENUM_DECLARATION      CPP_ENUMDEF_DECLARATION
#define PG_CPP_DOMAIN_DECLARATION    CPP_ALIASDEF_DECLARATION


#define PG_CPP_INVOKABLE_DECLARATION(FUNC_DEF)\
struct T_NAME(T_NAMETUPLE(FUNC_DEF))\
{\
    static std::vector<std::string_view> overloads;\
}

#endif
