#ifndef TEST_APP_TYPES
#define TEST_APP_TYPES


#include "core_pg_bindings/types.hpp"
#include "test_app/definition.hpp"


namespace pg = core_pg_bindings;
// DEBUG clear && g++ -P -E -I/usr/include/boost -I../../../../../../../python/core/core_types/core_types/cpp -I../../../../../../core_pg_bindings/cpp -I../../../../../../../../../dev/usr/include -I./ types.hpp


namespace test_app 
{

PG_CPP_TABLE_DECLARATION(TEST_APP_AUTHOR);
PG_CPP_TABLE_DECLARATION(TEST_APP_AUTHORED);
PG_CPP_TABLE_DECLARATION(TEST_APP_WITH_TIMESTAMPS);
PG_CPP_ENUM_DECLARATION(TEST_APP_POST_STATUS);
PG_CPP_TABLE_DECLARATION(TEST_APP_POST);
PG_CPP_TABLE_DECLARATION(TEST_APP_COMMENT);
PG_CPP_TABLE_DECLARATION(TEST_APP_COMMENT_POST);
PG_CPP_TABLE_DECLARATION(TEST_APP_COMPOSITE_AUTHOR);


author create_author ();
std::optional<author> get_author_by_id (pg::int8& p_author_id);
std::optional<std::vector<post>> get_author_posts (pg::int8& p_author_id);
std::vector<post> get_author_posts (author& p_author);


std::optional<post> get_post_by_id (pg::int8& p_post_id);
std::optional<std::vector<comment>> get_post_comments (pg::int8& p_post_id);
std::vector<comment> get_post_comments (post& p_post);
std::optional<post> create_post (pg::int8& p_author_id, pg::text& p_content, pg::text& p_title);
post create_post (author& p_author, pg::text& p_content, pg::text& p_title);
std::optional<comment> create_comment (pg::int8& p_author_id, pg::int8& p_post_id, pg::text& p_content);
comment create_comment (author& p_author, post& p_post, pg::text& p_content);
std::optional<test_app::comment_post> as_comment_post(pg::int8& p_post_id, pg::int8& p_comment_id, pg::text& p_description, pg::int8& p_author_id);
comment_post as_comment_post(post& p_post, comment& p_comment, pg::text& p_description, author& p_author);

};


namespace pqxx 
{

PG_DECLARE_TABLE_CONVERSION(TEST_APP_AUTHOR);
PG_DECLARE_TABLE_CONVERSION(TEST_APP_AUTHORED);
PG_DECLARE_TABLE_CONVERSION(TEST_APP_WITH_TIMESTAMPS);
PG_DECLARE_ENUM_CONVERSION(TEST_APP_POST_STATUS);
PG_DECLARE_TABLE_CONVERSION(TEST_APP_POST);
PG_DECLARE_TABLE_CONVERSION(TEST_APP_COMMENT);
PG_DECLARE_COMPOSITE_CONVERSION(TEST_APP_COMMENT_POST);
PG_DECLARE_COMPOSITE_CONVERSION(TEST_APP_COMPOSITE_AUTHOR);

};


#endif // TEST_APP_TYPES
