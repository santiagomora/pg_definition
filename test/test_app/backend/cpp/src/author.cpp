#include "core_pg_bindings/typing/types.hpp"
#include "core_pg_bindings/execution/invokable.hpp"

#include "test_app/author.hpp"
#include "test_app/database/types.hpp"
#include "test_app/environment.hpp"


namespace pg = core_pg_bindings;
namespace ta = test_app;


std::shared_ptr<pg::query_configuration> ta::create_author::query_config () const
{
    return std::make_shared<pg::query_configuration>(
        "SELECT create_author()", ta::database_env::env()
    );
}


std::shared_ptr<pg::query_configuration> ta::get_author_by_id::query_config () const
{
    return std::make_shared<pg::query_configuration>(
        "SELECT a from author a WHERE id = $1 LIMIT 1", ta::database_env::env()
    );
}


std::shared_ptr<pg::query_configuration> ta::get_author_posts::query_config () const
{
    return std::make_shared<pg::query_configuration>(
        "SELECT get_author_posts(p_author := $1)", ta::database_env::env()
    );
}


std::optional<ta::get_author_posts::ResultType> ta::get_author_posts::operator() (
    const pg::int8& p_author_id
)
{
    std::optional<ta::author> v_author = ta::get_author_by_id{}(p_author_id);
    if (v_author.has_value())
    {
        return ta::get_author_posts{}(v_author.value());
    }
    return std::nullopt;
}
