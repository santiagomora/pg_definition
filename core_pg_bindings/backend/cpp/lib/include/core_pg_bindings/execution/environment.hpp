#ifndef CORE_PG_BINDINGS_EXECUTION_ENVIRONMENT
#define CORE_PG_BINDINGS_EXECUTION_ENVIRONMENT


namespace core_pg_bindings
{

class db_environment
{
public:
    std::string conn_str;
    std::string search_path;
    db_environment(std::string conn_str, std::string search_path)
        : conn_str(conn_str), search_path(search_path)
    {}
};

}

#endif
