#include "core_pg_bindings/execution/invokable.hpp"
#include "test_app/api/environment.hpp"


namespace ta = test_app;
namespace pg = core_pg_bindings;


std::optional<pg::db_environment> ta::database_env::_env = std::nullopt;


pg::db_environment& ta::database_env::env ()
{
    if (!ta::database_env::_env.has_value()){
        ta::database_env::_env = pg::db_environment("host=172.18.0.1 dbname=mutzhub port=5432 user=mutzhub password=WtbNMMpX46iynzjVobrh8Qu7omvFIL9JEvbkLYYCpCJNIwDWnBwcVquhk6vXe6En", "test_app");
    }
    return ta::database_env::_env.value();
}
