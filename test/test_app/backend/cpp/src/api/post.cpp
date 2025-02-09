#include "core_pg_bindings/typing/types.hpp"
#include "core_pg_bindings/execution/invokable.hpp"

#include "test_app/api/post.hpp"
#include "test_app/typing/types.hpp"
#include "test_app/api/environment.hpp"


namespace pg = core_pg_bindings;
namespace ta = test_app;


std::shared_ptr<pg::query_configuration> ta::get_post_by_id::query_config () const
{
    return std::make_shared<pg::query_configuration>(
        "SELECT p from post p WHERE id = $1 LIMIT 1", ta::database_env::env()
    );
}


std::shared_ptr<pg::query_configuration> ta::get_post_comments::query_config () const
{
    return std::make_shared<pg::query_configuration>(
        "SELECT get_post_comments(p_post := $1)", ta::database_env::env()
    );
}


std::optional<std::vector<ta::comment>> ta::get_post_comments::operator() (
    const pg::int8& p_post_id
)
{
    std::optional<ta::post> v_post = ta::get_post_by_id{}(p_post_id);
    if (v_post.has_value())
    {
        return ta::get_post_comments{}(v_post.value());
    }
    return std::nullopt;
}


std::shared_ptr<pg::query_configuration> ta::create_post::query_config () const
{
    return std::make_shared<pg::query_configuration>(
        "SELECT create_post(p_author := $1, p_content := $2, p_title := $3)", ta::database_env::env()
    );
}


std::optional<ta::post> ta::create_post::operator() (
    const pg::int8& p_author_id, const pg::text& p_content, const pg::text& p_title
)
{
    std::optional<ta::author> v_author = ta::get_author_by_id{}(p_author_id);
    if (v_author.has_value())
    {
        return ta::create_post{}(v_author.value(), p_content, p_title);
    }
    return std::nullopt;
}


std::shared_ptr<pg::query_configuration> ta::create_comment::query_config () const
{
    return std::make_shared<pg::query_configuration>(
        "SELECT create_comment(p_author := $1, p_post := $2, p_content := $3)", ta::database_env::env()
    );
}


std::optional<ta::comment> ta::create_comment::operator() (
    const pg::int8& p_author_id, const pg::int8& p_post_id, const pg::text& p_content
)
{
    std::optional<ta::author> v_author = ta::get_author_by_id{}(p_author_id);
    std::optional<ta::post> v_post = ta::get_post_by_id{}(p_post_id);
    if (v_author.has_value() && v_post.has_value())
    {
        return ta::create_comment{}(v_author.value(), v_post.value(), p_content);
    }
    return std::nullopt;
}


std::shared_ptr<pg::query_configuration> ta::as_comment_post::query_config () const
{
    return std::make_shared<pg::query_configuration>(
        "SELECT as_comment_post(p_post := $1, p_comment := $2, p_description := $3, p_author := $4)", ta::database_env::env()
    );
}


std::optional<ta::comment_post> ta::as_comment_post::operator() (
    const pg::int8& p_post_id, const pg::int8& p_comment_id, const pg::text& p_description,
    const pg::int8& p_author_id
)
{
    std::optional<ta::author> v_author = ta::get_author_by_id{}(p_author_id);
    std::optional<ta::post> v_post = ta::get_post_by_id{}(p_post_id);
    std::optional<std::vector<test_app::comment>> v_comments = test_app::get_post_comments{}(p_post_id);
    if (v_author.has_value() && v_post.has_value() && v_comments.has_value() && v_comments->size() > 0)
    {
        return ta::as_comment_post{}(v_post.value(), v_comments.value()[0], p_description, v_author.value());
    }
    return std::nullopt;
}
