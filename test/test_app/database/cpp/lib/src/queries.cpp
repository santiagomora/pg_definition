#include "core_pg_bindings/typing/types.hpp"
#include "core_pg_bindings/execution/invokable.hpp"
#include "test_app/database/interface/types.hpp"
#include "test_app/database/interface/queries.hpp"


namespace ta = test_app::database::queries;
namespace db = test_app::database;
namespace pg = core_pg_bindings;


std::optional<pg::db_environment> db::environment::_env = std::nullopt;


pg::db_environment& db::environment::env ()
{
    if (!db::environment::_env.has_value()){
        db::environment::_env = pg::db_environment("host=172.18.0.1 dbname=mutzhub port=5432 user=mutzhub password=WtbNMMpX46iynzjVobrh8Qu7omvFIL9JEvbkLYYCpCJNIwDWnBwcVquhk6vXe6En", "test_app");
    }
    return db::environment::_env.value();
}


/*
std::optional<ta::get_post_comments::ResultType> ta::get_post_comments::operator() (
    pqxx::work& tx, const pg::int8 p_post_id
)
{
    std::optional<db::post> v_post = ta::get_post_by_id{}(tx, p_post_id);
    if (v_post.has_value())
    {
        return ta::get_post_comments{}(tx, v_post.value());
    }
    return std::nullopt;
}


std::optional<ta::get_author_posts::ResultType> ta::get_author_posts::operator() (
    pqxx::work& tx, const pg::int8 p_author_id
)
{
    std::optional<db::author> v_author = ta::get_author_by_id{}(tx, p_author_id);
    if (v_author.has_value())
    {
        return ta::get_author_posts{}(tx, v_author.value());
    }
    return std::nullopt;
}


std::optional<ta::create_post::ResultType> ta::create_post::operator() (
    pqxx::work& tx, const pg::int8 p_author_id, const pg::text p_content,
    const pg::text p_title
)
{
    std::optional<db::author> v_author = ta::get_author_by_id{}(tx, p_author_id);
    if (v_author.has_value())
    {
        return ta::create_post{}(tx, v_author.value(), p_content, p_title);
    }
    return std::nullopt;
}


std::optional<ta::create_comment::ResultType> ta::create_comment::operator() (
    pqxx::work& tx, const pg::int8 p_author_id, const pg::int8 p_post_id,
    const pg::text p_content
)
{
    std::optional<db::author> v_author = ta::get_author_by_id{}(tx, p_author_id);
    std::optional<db::post> v_post = ta::get_post_by_id{}(tx, p_post_id);
    if (v_author.has_value() && v_post.has_value())
    {
        return ta::create_comment{}(tx, v_author.value(), v_post.value(), p_content);
    }
    return std::nullopt;
}


std::optional<ta::as_comment_post::ResultType> ta::as_comment_post::operator() (
    pqxx::work& tx, const pg::int8 p_post_id, const pg::int8 p_comment_id,
    const pg::text p_description, const pg::int8 p_author_id
)
{
    std::optional<db::author> v_author = ta::get_author_by_id{}(tx, p_author_id);
    std::optional<db::post> v_post = ta::get_post_by_id{}(tx, p_post_id);
    std::optional<std::vector<db::comment>> v_comments = ta::get_post_comments{}(tx, p_post_id);
    if (v_author.has_value() && v_post.has_value() && v_comments.has_value() && v_comments->size() > 0)
    {
        return ta::as_comment_post{}(tx, v_post.value(), v_comments.value()[0], p_description, v_author.value());
    }
    return std::nullopt;
}*/
