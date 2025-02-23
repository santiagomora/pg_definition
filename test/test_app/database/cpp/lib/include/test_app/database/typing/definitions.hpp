#ifndef TEST_APP_DATABASE_TYPING_DEFINITIONS
#define TEST_APP_DATABASE_TYPING_DEFINITIONS
#include "core_types/typing/backend.hpp"
#include "core_pg_bindings/macros/declaration.hpp"
#include "core_pg_bindings/macros/definition.hpp"


#define TEST_APP_DB_AUTHOR PG_TABLE_DEFINITION(\
    TEST_APP_DB_AUTHOR,\
    (test_app::database, author),\
    (PG_COLUMN(PG_INT8, id))\
    (PG_COLUMN(PG_TEXT, name)),\
    NONE,\
    (test_app::database::interface, author)\
)
#define TEST_APP_DB_AUTHOR_MEMBERS T_MEMBERS(TEST_APP_DB_AUTHOR)
#define TEST_APP_DB_AUTHOR_CONSTRUCTORS (TEST_APP_DB_AUTHOR)


#define TEST_APP_DB_AUTHORED PG_TABLE_DEFINITION(\
    TEST_APP_DB_AUTHORED,\
    (test_app::database, authored),\
    (PG_COLUMN(PG_INT8, author_id))\
    (PG_COLUMN(PG_TEXT, content)),\
    NONE,\
    (test_app::database::interface, authored)\
)
#define TEST_APP_DB_AUTHORED_MEMBERS T_MEMBERS(TEST_APP_DB_AUTHORED)
#define TEST_APP_DB_AUTHORED_CONSTRUCTORS (TEST_APP_DB_AUTHORED)


#define TEST_APP_DB_WITH_TIMESTAMPS PG_TABLE_DEFINITION(\
    TEST_APP_DB_WITH_TIMESTAMPS,\
    (test_app::database, with_timestamps),\
    (PG_COLUMN(PG_TIMESTAMPTZ, created_at))\
    (PG_COLUMN(PG_TIMESTAMPTZ, updated_at)),\
    NONE,\
    (test_app::database::interface, with_timestamps)\
)
#define TEST_APP_DB_WITH_TIMESTAMPS_MEMBERS T_MEMBERS(TEST_APP_DB_WITH_TIMESTAMPS)
#define TEST_APP_DB_WITH_TIMESTAMPS_CONSTRUCTORS (TEST_APP_DB_WITH_TIMESTAMPS)


#define TEST_APP_DB_POST_STATUS PG_ENUM_DEFINITION(\
    TEST_APP_DB_POST_STATUS,\
    (test_app::database, post_status),\
    (PG_ENUM_VALUE(published))\
    (PG_ENUM_VALUE(waiting_approval))\
    (PG_ENUM_VALUE(draft)),\
    (test_app::database::interface, post_status)\
)
#define TEST_APP_DB_POST_STATUS_CONSTRUCTORS (TEST_APP_DB_POST_STATUS)


#define TEST_APP_DB_POST PG_TABLE_DEFINITION(\
    TEST_APP_DB_POST,\
    (test_app::database, post),\
    (PG_COLUMN(PG_INT8, id))\
    (PG_COLUMN(PG_TEXT, title))\
    (PG_COLUMN(TEST_APP_DB_POST_STATUS, status)),\
    (TEST_APP_DB_AUTHORED)(TEST_APP_DB_WITH_TIMESTAMPS),\
    (test_app::database::interface, post)\
)
#define TEST_APP_DB_POST_MEMBERS TEST_APP_DB_AUTHORED_MEMBERS\
    TEST_APP_DB_WITH_TIMESTAMPS_MEMBERS\
    T_MEMBERS(TEST_APP_DB_POST)
#define TEST_APP_DB_POST_CONSTRUCTORS (TEST_APP_DB_POST)


#define TEST_APP_DB_COMMENT PG_TABLE_DEFINITION(\
    TEST_APP_DB_COMMENT,\
    (test_app::database, comment),\
    (PG_COLUMN(PG_INT8, id))\
    (PG_COLUMN(PG_INT8, post_id)),\
    (TEST_APP_DB_AUTHORED)(TEST_APP_DB_WITH_TIMESTAMPS),\
    (test_app::database::interface, comment)\
)
#define TEST_APP_DB_COMMENT_MEMBERS TEST_APP_DB_AUTHORED_MEMBERS\
    TEST_APP_DB_WITH_TIMESTAMPS_MEMBERS\
    T_MEMBERS(TEST_APP_DB_COMMENT)
#define TEST_APP_DB_COMMENT_CONSTRUCTORS (TEST_APP_DB_COMMENT)


#define TEST_APP_DB_COMMENT_POST PG_COMPOSITE_DEFINITION(\
    TEST_APP_DB_COMMENT_POST,\
    (test_app::database, comment_post),\
    (PG_ATTRIBUTE(TEST_APP_DB_COMMENT, comment))\
    (PG_ATTRIBUTE(TEST_APP_DB_POST, post))\
    (PG_ATTRIBUTE(PG_TEXT, description))\
    (PG_ATTRIBUTE(TEST_APP_DB_AUTHOR, author)),\
    (test_app::database::interface, comment_post)\
)
#define TEST_APP_DB_COMMENT_POST_MEMBERS T_MEMBERS(TEST_APP_DB_COMMENT_POST)
#define TEST_APP_DB_COMMENT_POST_CONSTRUCTORS (TEST_APP_DB_COMMENT_POST)


#define TEST_APP_DB_COMPOSITE_AUTHOR PG_COMPOSITE_DEFINITION(\
    TEST_APP_DB_COMPOSITE_AUTHOR,\
    (test_app::database, composite_author),\
    (PG_ATTRIBUTE(PG_INT8, id))\
    (PG_ATTRIBUTE(PG_TEXT, biography))\
    (PG_ATTRIBUTE(PG_TEXT, name)),\
    (test_app::database::interface, composite_author)\
)
#define TEST_APP_DB_COMPOSITE_AUTHOR_MEMBERS T_MEMBERS(TEST_APP_DB_COMPOSITE_AUTHOR)
#define TEST_APP_DB_COMPOSITE_AUTHOR_CONSTRUCTORS (TEST_APP_DB_COMPOSITE_AUTHOR)


#define TEST_APP_DB_DOMAIN PG_TYPE_DOMAIN_DEFINITION(\
    TEST_APP_DB_DOMAIN,\
    (test_app::database, domain),\
    PG_INT8,\
    (test_app::database::interface, domain)\
)
#define TEST_APP_DB_DOMAIN_CONSTRUCTORS (TEST_APP_DB_DOMAIN) PG_INT8_CONSTRUCTORS
#define TEST_APP_DB_DOMAIN_INHERITANCE_CHAIN PG_INT8_INHERITANCE_CHAIN (TEST_APP_DB_DOMAIN)


#define TEST_APP_DB_GET_AUTHOR_POSTS PG_INVOKABLE(\
    TEST_APP_DB_GET_AUTHOR_POSTS,\
    (test_app::database, get_author_posts)\
)


#define TEST_APP_DB_CREATE_POST PG_INVOKABLE(\
    TEST_APP_DB_CREATE_POST,\
    (test_app::database, create_post)\
)


#define TEST_APP_DB_CREATE_COMMENT PG_INVOKABLE(\
    TEST_APP_DB_CREATE_COMMENT,\
    (test_app::database, create_comment)\
)


#define TEST_APP_DB_GET_POST_COMMENTS PG_INVOKABLE(\
    TEST_APP_DB_GET_POST_COMMENTS,\
    (test_app::database, get_post_comments)\
)


#define TEST_APP_DB_AS_COMMENT_POST PG_INVOKABLE(\
    TEST_APP_DB_AS_COMMENT_POST,\
    (test_app::database, as_comment_post)\
)


#define TEST_APP_DB_CREATE_AUTHOR PG_INVOKABLE(\
    TEST_APP_DB_CREATE_AUTHOR,\
    (test_app::database, create_author)\
)


#endif
