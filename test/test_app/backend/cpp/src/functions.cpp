#include "test_app/backend/functions.hpp"


namespace ct = core_types;
namespace db = test_app::database;
namespace ta = test_app;


std::optional<ct::text> ta::get_author_name (const ct::int8& p_author_id)
{
    pg::db_environment& env = db::environment::env();
    pqxx::connection conn(env.conn_str);
    pqxx::work tx(conn);
    tx.exec(std::string("SET search_path TO ") + env.search_path).no_rows();
    std::optional<db::author> v_res = db::get_author_by_id{}(tx, p_author_id);
    tx.commit();
    if (v_res.has_value())
    {
        return v_res->name;
    }
    return std::nullopt;
}




std::optional<ct::text> ta::get_author_name (const ct::int8& p_author_id)
{
    pg::db_environment& env = db::environment::env();
    pqxx::connection conn(env.conn_str);
    pqxx::work tx(conn);
    tx.exec(std::string("SET search_path TO ") + env.search_path).no_rows();
    std::optional<db::author> v_res = db::get_author_by_id{}(tx, p_author_id);
    tx.commit();
    if (v_res.has_value())
    {
        return v_res->name;
    }
    return std::nullopt;
}
