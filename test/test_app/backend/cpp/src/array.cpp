#include "core_pg_bindings/typing/types.hpp"
#include "core_pg_bindings/execution/invokable.hpp"

#include "test_app/database/types.hpp"
#include "test_app/environment.hpp"
#include "test_app/array.hpp"


namespace pg = core_pg_bindings;
namespace ta = test_app;


std::shared_ptr<pg::query_configuration> ta::test_array::query_config () const
{
    return std::make_shared<pg::query_configuration>(
        "SELECT '{1,2,3,4,5,6}'::int8[]", ta::database_env::env()
    );
}
