#ifndef TEST_APP_DATABASE_INTERFACE_QUERIES
#define TEST_APP_DATABASE_INTERFACE_QUERIES
#include "core_pg_bindings/execution/environment.hpp"
#include "core_pg_bindings/execution/invokable.hpp"
#include "test_app/database/typing/namespace.hpp"
#include "test_app/database/interface/types.hpp"


namespace pg = core_pg_bindings;


namespace test_app
{

}

namespace test_app::database
{

class environment
{
private:
    static std::optional<pg::db_environment> _env;
public:
    static pg::db_environment& env ();
};

}

namespace test_app::database::queries
{

struct create_author
    : public pg::queries_database_on_transaction<
          pg::fetch_one_functor,
          pg::SingleResult_<author>>
{
    constexpr std::string_view query() const override
    {
        return "select create_author();"; 
    };
};


struct get_author_by_id
    : public pg::queries_database_on_transaction<
          pg::fetch_one_functor,
          pg::OptionalResult_<pg::SingleResult_<author>>,
          const pg::int8>
{
    constexpr std::string_view query() const override 
    {
        return "SELECT a from author a WHERE id = $1 LIMIT 1"; 
    };
};


class get_author_posts
    : public pg::queries_database_on_transaction<
          pg::fetch_many_functor,
          pg::ContainedResult_<post>,
          const author&>
{
    constexpr std::string_view query() const override 
    {
        return "SELECT get_author_posts(p_author := $1)";
    };
};


class get_post_by_id
    : public pg::queries_database_on_transaction<
          pg::fetch_one_functor,
          pg::OptionalResult_<pg::SingleResult_<post>>,
          const pg::int8&>
{
    constexpr std::string_view query() const override 
    {
        return "SELECT p from post p WHERE id = $1 LIMIT 1";
    };
};


class get_post_comments
    : public pg::queries_database_on_transaction<
          pg::fetch_many_functor,
          pg::ContainedResult_<comment>,
          const post&>
{
    constexpr std::string_view query() const override 
    {
        return "SELECT get_post_comments(p_post := $1)";
    };
};


class create_post
    : public pg::queries_database_on_transaction<
          pg::fetch_one_functor, pg::SingleResult_<post>,
          const author&, const pg::text&, const pg::text&>
{
    constexpr std::string_view query() const override 
    {
        return "SELECT create_post(p_author := $1, p_content := $2, p_title := $3)";
    };
};


class create_comment
    : public pg::queries_database_on_transaction<
          pg::fetch_one_functor, pg::SingleResult_<comment>,
          const author&, const post&, const pg::text&>
{
    constexpr std::string_view query() const override 
    {
        return "SELECT create_comment(p_author := $1, p_post := $2, p_content := $3)";
    };
};


class as_comment_post
    : public pg::queries_database_on_transaction<
          pg::fetch_one_functor, pg::SingleResult_<comment_post>,
          const post&, const comment&, const pg::text&, const author&>
{
    constexpr std::string_view query() const override 
    {
        return "SELECT as_comment_post(p_post := $1, p_comment := $2, p_description := $3, p_author := $4)";
    };
};

}

#endif
