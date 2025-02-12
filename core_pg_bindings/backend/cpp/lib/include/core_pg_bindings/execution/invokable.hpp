#ifndef CORE_PG_BINDINGS_EXECUTION_INVOKABLE
#define CORE_PG_BINDINGS_EXECUTION_INVOKABLE
#include <exception>
#include <pqxx/pqxx>
#include "core_pg_bindings/execution/environment.hpp"
#include "core_pg_bindings/execution/functors.hpp"


namespace core_pg_bindings
{

class query_configuration
{
public:
    std::string query;
    db_environment& environment;
    query_configuration(std::string&& query, db_environment& environment)
    : query(query), environment(environment)
    {}
};


class has_query_configuration
{
private:
    std::optional<std::shared_ptr<query_configuration>> _stored_config = std::nullopt;
protected:
    std::shared_ptr<query_configuration> stored_config ()
    {
        if (!_stored_config.has_value())
        {
            _stored_config = query_config();
        }
        return _stored_config.value();
    }
    virtual std::shared_ptr<query_configuration> query_config() const = 0;
};


template<template <typename, typename...> class FT, typename T, typename... Args>
class queries_database_on_transaction
    : public has_query_configuration
{
public:
    using ResultType = typename T::Container;
    using BaseType = queries_database_on_transaction<FT, T, Args...>;
    ResultType operator() (
        pqxx::work& tx, Args... args
    )
    {
        ResultType v_res;
        try
        {
            FT<T, Args...> ft;
            std::tuple<Args...> arguments  = std::make_tuple<Args...>(args...);
            std::string query = stored_config()->query;
            v_res = ft(query, tx, arguments);
        }
        catch (std::exception const &e) 
        {
            // uncaught exception, log then throw
            std::cerr << e.what() << std::endl;
            throw e;
        }
        return v_res;
    };
};


// template<template <typename, typename...> class FT, typename T, typename... Args>
// class queries_database_on_connection
//     : public has_query_configuration
// {
// public:
//     using ResultType = typename T::Container;
//     using BaseType = queries_database_on_transaction<FT, T, Args...>;
//     using queries_database_on_transaction<FT, T, Args...>::operator();
//     ResultType operator() (
//         Args... args
//     )
//     {
//         ResultType v_res;
//         try
//         {
//             db_environment& env = stored_config()->environment;
//             pqxx::connection conn(env.conn_str);
//             pqxx::work tx(conn);
//             tx.exec(std::string("SET search_path TO ") + env.search_path).no_rows();
//             FT<T, Args...> ft;
//             std::tuple<Args...> arguments  = std::make_tuple<Args...>(args...);
//             std::string query = stored_config()->query;
//             v_res = ft(query, tx, arguments);
//             tx.commit();
//             return v_res;
//         }
//         catch (std::exception const &e) 
//         {
//             // uncaught exception, log then throw
//             std::cerr << e.what() << std::endl;
//             throw e;
//         }
//         return v_res;
//     };
// };

}


#endif
