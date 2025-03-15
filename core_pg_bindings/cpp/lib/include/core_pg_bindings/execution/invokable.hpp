#ifndef CORE_PG_BINDINGS_EXECUTION_INVOKABLE
#define CORE_PG_BINDINGS_EXECUTION_INVOKABLE
#include <exception>
#include <pqxx/pqxx>
#include "core_types/typing/backend.hpp"
#include "core_types/typing/interface.hpp"
#include "core_pg_bindings/execution/environment.hpp"
#include "core_pg_bindings/execution/functors.hpp"


namespace ct = core_types;


namespace core_pg_bindings
{


template<typename Derived, template <typename, typename...> class FT, typename T>
struct queries_database_on_transaction
{
    using ResultType = typename T::Container;
    template<typename... Args> static ResultType query (
        pqxx::dbtransaction& tx, Args&... args
    )
    {
        ResultType v_res;
        std::string_view query = Derived::query_string(args...);
        std::tuple<Args...> arguments = std::make_tuple(args...);
        try
        {
            FT<T, Args...> ft;
            v_res = ft(tx,  query, arguments);
        }
        catch (std::exception const &e)
        {
            std::cerr << e.what() << std::endl;
            std::cerr << "CALLED QUERY: " << query << "\nWITH PARAMETERS: " << ct::to_str(arguments) << std::endl;
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
