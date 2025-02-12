#ifndef TEST_APP_API_ENVIRONMENT
#define TEST_APP_API_ENVIRONMENT
#include "core_pg_bindings/execution/environment.hpp"
#include "core_pg_bindings/execution/invokable.hpp"


namespace pg = core_pg_bindings;


namespace test_app
{

class database_env
{
private:
    static std::optional<pg::db_environment> _env;
public:
    static pg::db_environment& env ();
};


}

#endif
