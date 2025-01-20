#ifndef TEST_APP_MACROS_DEFINITIONS
#define TEST_APP_MACROS_DEFINITIONS


#include "base_types/include/macros/definition.hpp"
// #include "base_types/include/macros/register.hpp"
#include "base_types/include/types.hpp"


#define TEST_APP_AUTHOR DATACLASS_DEFINITION(\
    TEST_APP_AUTHOR,\
    (test_app, author),\
    (DATACLASS_MEMBER(btp, int8_py, id))\
    (DATACLASS_MEMBER(btp, text_py, name)),\
    BOOST_PP_EMPTY()\
)
#define TEST_APP_AUTHOR_MEMBERS T_DIRECT_MEMBERS(TEST_APP_AUTHOR)


#define TEST_APP_AUTHORED DATACLASS_DEFINITION(\
    TEST_APP_AUTHORED,\
    (test_app, authored),\
    (DATACLASS_MEMBER(btp, int8_py, author_id))\
    (DATACLASS_MEMBER(btp, text_py, content)),\
    BOOST_PP_EMPTY()\
)
#define TEST_APP_AUTHORED_MEMBERS T_DIRECT_MEMBERS(TEST_APP_AUTHORED)


#define TEST_APP_WITH_TIMESTAMPS DATACLASS_DEFINITION(\
    TEST_APP_WITH_TIMESTAMPS,\
    (test_app, with_timestamps),\
    (DATACLASS_MEMBER(btp, timestamptz_py, created_at))\
    (DATACLASS_MEMBER(btp, timestamptz_py, updated_at)),\
    BOOST_PP_EMPTY()\
)
#define TEST_APP_WITH_TIMESTAMPS_MEMBERS T_DIRECT_MEMBERS(TEST_APP_WITH_TIMESTAMPS)


#define TEST_APP_POST_STATUS ENUM_DEFINITION(\
    TEST_APP_POST_STATUS,\
    (test_app, post_status),\
    (ENUM_MEMBER(published))\
    (ENUM_MEMBER(waiting_approval))\
    (ENUM_MEMBER(draft))\
)


#define TEST_APP_POST DATACLASS_DEFINITION(\
    TEST_APP_POST,\
    (test_app, post),\
    (DATACLASS_MEMBER(btp, int8_py, id))\
    (DATACLASS_MEMBER(btp, text_py, title))\
    (DATACLASS_MEMBER(test_app, post_status, status)),\
    (TEST_APP_AUTHORED)(TEST_APP_WITH_TIMESTAMPS)\
)
#define TEST_APP_POST_MEMBERS T_DIRECT_MEMBERS(TEST_APP_POST)\
    TEST_APP_AUTHORED_MEMBERS\
    TEST_APP_WITH_TIMESTAMPS_MEMBERS


#define TEST_APP_COMMENT DATACLASS_DEFINITION(\
    TEST_APP_COMMENT,\
    (test_app, comment),\
    (DATACLASS_MEMBER(btp, int8_py, id))\
    (DATACLASS_MEMBER(btp, int8_py, post_id)),\
    (TEST_APP_AUTHORED)(TEST_APP_WITH_TIMESTAMPS)\
)
#define TEST_APP_COMMENT_MEMBERS T_DIRECT_MEMBERS(TEST_APP_COMMENT)\
    TEST_APP_AUTHORED_MEMBERS\
    TEST_APP_WITH_TIMESTAMPS_MEMBERS


#define TEST_APP_COMMENT_POST DATACLASS_DEFINITION(\
    TEST_APP_COMMENT_POST,\
    (test_app, comment_post),\
    (DATACLASS_MEMBER(test_app, comment, comment))\
    (DATACLASS_MEMBER(test_app, post, post))\
    (DATACLASS_MEMBER(btp, text_py, description))\
    (DATACLASS_MEMBER(test_app, author, author)),\
    BOOST_PP_EMPTY()\
)

#define TEST_APP_COMMENT_POST_MEMBERS T_DIRECT_MEMBERS(TEST_APP_COMMENT_POST)


#define TEST_APP_COMPOSITE_AUTHOR DATACLASS_DEFINITION(\
    TEST_APP_COMPOSITE_AUTHOR,\
    (test_app, composite_author),\
    (DATACLASS_MEMBER(btp, int8_py, id))\
    (DATACLASS_MEMBER(btp, text_py, biography))\
    (DATACLASS_MEMBER(btp, text_py, name)),\
    BOOST_PP_EMPTY()\
)

#define TEST_APP_COMPOSITE_AUTHOR_MEMBERS T_DIRECT_MEMBERS(TEST_APP_COMPOSITE_AUTHOR)

// #define TEST_APP_DOMAIN ALIAS_DEFINITION(
//     TEST_APP_DOMAIN,
//     (test_app, domain),
//     INT8_PY
// )

// #define TEST_APP_DOMAIN_CONSTRUCTORS (TEST_APP_DOMAIN) INT8_PY_CONSTRUCTORS

#endif
