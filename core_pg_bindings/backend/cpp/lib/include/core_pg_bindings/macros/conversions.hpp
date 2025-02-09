#ifndef CORE_PG_BINDINGS_MACROS_CONVERSIONS
#define CORE_PG_BINDINGS_MACROS_CONVERSIONS
#include "core_types/macros/definition.hpp"


#define _PG_TYPEDEF_CONVERSION(TYPE_DEF, BUF_SIZE)\
template<>\
std::string const type_name<T_QUALNAME(T_NAMETUPLE(TYPE_DEF))>{BOOST_PP_STRINGIZE(T_QUALNAME(T_NAMETUPLE(TYPE_DEF)))};\
template<>\
struct nullness<T_QUALNAME(T_NAMETUPLE(TYPE_DEF))> : pqxx::no_null<T_QUALNAME(T_NAMETUPLE(TYPE_DEF))> {};\
template<>\
struct string_traits<T_QUALNAME(T_NAMETUPLE(TYPE_DEF))> {\
    static constexpr bool converts_to_string {true};\
    static constexpr bool converts_from_string {true};\
    static zview to_buf (char *begin, char *end, const T_QUALNAME(T_NAMETUPLE(TYPE_DEF)) &value) {\
        return string_traits<std::string>::to_buf(begin, end, value.to_string());\
    }\
    static char *into_buf (char *begin, char *end, const T_QUALNAME(T_NAMETUPLE(TYPE_DEF)) &value) {\
        std::string as_string = value.to_string();\
        if (std::cmp_greater_equal(std::size(as_string), end - begin))\
            throw conversion_error{"Could not convert string to string: too long for buffer."};\
        as_string.copy(begin, std::size(as_string));\
        begin[std::size(as_string)] = '\0';\
        return begin + std::size(as_string) + 1;\
    }\
    static std::size_t size_buffer (\
        const T_QUALNAME(T_NAMETUPLE(TYPE_DEF)) BOOST_PP_IF(BOOST_PP_IS_EMPTY(BUF_SIZE), &value, BOOST_PP_EMPTY())\
    ) noexcept {\
        return BOOST_PP_IF(\
            BOOST_PP_IS_EMPTY(BUF_SIZE),\
            string_traits<T_BASE_PRIMITIVE(TYPE_DEF)>::size_buffer(value.value()),\
            BUF_SIZE);\
    }\
    static T_QUALNAME(T_NAMETUPLE(TYPE_DEF)) from_string (std::string_view text) {\
        return T_QUALNAME(T_NAMETUPLE(TYPE_DEF))(string_traits<std::string>::from_string(text));\
    }\
}


#define _PG_ENUMDEF_CONVERSION(ENUM_DEF)\
template<>\
std::string const type_name<ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF)>{BOOST_PP_STRINGIZE(ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF))};\
template<>\
struct nullness<ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF)> : pqxx::no_null<ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF)> {};\
template<>\
struct string_traits<ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF)> {\
    static constexpr bool converts_to_string {true};\
    static constexpr bool converts_from_string {true};\
    static zview to_buf (char *begin, char *end, const ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF) &value) {\
        return string_traits<std::string>::to_buf(begin, end, T_QUALNAME(T_NAMETUPLE(ENUM_DEF))::static_to_string(value));\
    }\
    static char *into_buf (char *begin, char *end, const ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF) &value) {\
        return string_traits<std::string>::into_buf(begin, end, T_QUALNAME(T_NAMETUPLE(ENUM_DEF))::static_to_string(value));\
    }\
    static std::size_t size_buffer (\
        const ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF) &value\
    ) noexcept {\
        return string_traits<std::string>::size_buffer(T_QUALNAME(T_NAMETUPLE(ENUM_DEF))::static_to_string(value));\
    }\
    static ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF) from_string (std::string_view text) {\
        BOOST_PP_SEQ_FOR_EACH_I(ED_FROM_STRING_CASE, (ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF), text), ENUM_MEMBERS(ENUM_DEF))\
        throw pqxx::conversion_error(std::string("could not convert ") + static_cast<std::string>(text) + " to enum " + BOOST_PP_STRINGIZE(ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF)));\
    }\
};\
template<>\
std::string const type_name<T_QUALNAME(T_NAMETUPLE(ENUM_DEF))>{BOOST_PP_STRINGIZE(T_QUALNAME(T_NAMETUPLE(ENUM_DEF)))};\
template<>\
struct nullness<T_QUALNAME(T_NAMETUPLE(ENUM_DEF))> : pqxx::no_null<T_QUALNAME(T_NAMETUPLE(ENUM_DEF))> {};\
template<>\
struct string_traits<T_QUALNAME(T_NAMETUPLE(ENUM_DEF))> {\
    static constexpr bool converts_to_string {true};\
    static constexpr bool converts_from_string {true};\
    static zview to_buf (char *begin, char *end, const T_QUALNAME(T_NAMETUPLE(ENUM_DEF)) &value) {\
        return string_traits<ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF)>::to_buf(begin, end, value.value());\
    }\
    static char *into_buf (char *begin, char *end, const T_QUALNAME(T_NAMETUPLE(ENUM_DEF)) &value) {\
        return string_traits<ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF)>::into_buf(begin, end, value.value());\
    }\
    static std::size_t size_buffer (\
        const T_QUALNAME(T_NAMETUPLE(ENUM_DEF)) &value\
    ) noexcept {\
        return string_traits<ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF)>::size_buffer(value.value());\
    }\
    static T_QUALNAME(T_NAMETUPLE(ENUM_DEF)) from_string (std::string_view text) {\
        return T_QUALNAME(T_NAMETUPLE(ENUM_DEF))(string_traits<ENUM_QUALIFIED_UNDERLYING_CLASS(ENUM_DEF)>::from_string(text));\
    }\
}


#define _PG_CLASSDEF_CONVERSION(CLASS_DEF)\
template<>\
std::string const type_name<T_QUALNAME(T_NAMETUPLE(CLASS_DEF))>{BOOST_PP_STRINGIZE(T_QUALNAME(T_NAMETUPLE(CLASS_DEF)))};\
template<>\
struct nullness<T_QUALNAME(T_NAMETUPLE(CLASS_DEF))> : pqxx::no_null<T_QUALNAME(T_NAMETUPLE(CLASS_DEF))> {};\
template<>\
struct string_traits<T_QUALNAME(T_NAMETUPLE(CLASS_DEF))> {\
    static constexpr bool converts_to_string {true};\
    static constexpr bool converts_from_string {true};\
    static char *into_buf (char *begin, char *end, const T_QUALNAME(T_NAMETUPLE(CLASS_DEF)) &value) {\
        return pqxx::composite_into_buf<BOOST_PP_SEQ_FOR_EACH_I(CL_MEMBER_TYPE, BOOST_PP_EMPTY(), C_ALL_MEMBERS(CLASS_DEF))>(begin, end, BOOST_PP_SEQ_FOR_EACH_I(CL_ACCESS_MEMBER, value, C_ALL_MEMBERS(CLASS_DEF)));\
    }\
    static std::size_t size_buffer (\
        const T_QUALNAME(T_NAMETUPLE(CLASS_DEF)) &value\
    ) noexcept {\
        return pqxx::composite_size_buffer<BOOST_PP_SEQ_FOR_EACH_I(CL_MEMBER_TYPE, BOOST_PP_EMPTY(), C_ALL_MEMBERS(CLASS_DEF))>(BOOST_PP_SEQ_FOR_EACH_I(CL_ACCESS_MEMBER, value, C_ALL_MEMBERS(CLASS_DEF)));\
    }\
    static zview to_buf (char *begin, char *end, const T_QUALNAME(T_NAMETUPLE(CLASS_DEF)) &value) {\
        return {begin, pqxx::string_traits<T_QUALNAME(T_NAMETUPLE(CLASS_DEF))>::into_buf(begin, end, value) - begin - 1};\
    }\
    static T_QUALNAME(T_NAMETUPLE(CLASS_DEF)) from_string (std::string_view text) {\
        BOOST_PP_SEQ_FOR_EACH(CL_MEMBER_DECLARATION, ;, C_ALL_MEMBERS(CLASS_DEF))\
        pqxx::parse_composite<BOOST_PP_SEQ_FOR_EACH_I(CL_MEMBER_TYPE, BOOST_PP_EMPTY(), C_ALL_MEMBERS(CLASS_DEF))>(text, BOOST_PP_SEQ_FOR_EACH_I(CL_MEMBER_NAME, BOOST_PP_EMPTY(), C_ALL_MEMBERS(CLASS_DEF)));\
        return T_QUALNAME(T_NAMETUPLE(CLASS_DEF))(BOOST_PP_SEQ_FOR_EACH_I(CL_MEMBER_NAME, BOOST_PP_EMPTY(), C_ALL_MEMBERS(CLASS_DEF)));\
    }\
}


#define PG_DECLARE_TYPE_CONVERSION _PG_TYPEDEF_CONVERSION
#define PG_DECLARE_ENUM_CONVERSION _PG_ENUMDEF_CONVERSION
#define PG_DECLARE_TABLE_CONVERSION _PG_CLASSDEF_CONVERSION
#define PG_DECLARE_COMPOSITE_CONVERSION _PG_CLASSDEF_CONVERSION


#endif
