#include "test_app/types.hpp"


namespace pg = core_pg_bindings;


test_app::author test_app::create_author () 
{
    test_app::author v_author;
    pqxx::connection cx(std::getenv("DB_DSN"));
    pqxx::work tx(cx);
    tx.exec("SET SEARCH_PATH TO test_app");
    pqxx::row result = tx.exec("SELECT create_author()").one_row();
    tx.commit();
    v_author = result[0].as<test_app::author>();
    return v_author;
}


std::optional<test_app::author> test_app::get_author_by_id (
    pg::int8& p_author_id
) {
    std::optional<test_app::author> v_author;
    try {
        pqxx::connection cx(std::getenv("DB_DSN"));
        pqxx::work tx(cx);
        tx.exec("SET SEARCH_PATH TO test_app");
        pqxx::row result = tx.exec(
            "SELECT a from author a WHERE id = $1 LIMIT 1",
            p_author_id
        ).one_row();
        tx.commit();
        v_author = result[0].as<test_app::author>();
    } catch (std::exception const &e) {
        std::cerr << e.what() << std::endl;
    }
    return v_author;
}


std::optional<std::vector<test_app::post>> test_app::get_author_posts (
    pg::int8& p_author_id
) {
    std::optional<test_app::author> v_author = test_app::get_author_by_id(p_author_id);
    if (v_author.has_value()){
        return test_app::get_author_posts(v_author.value());
    }
    return std::nullopt;
}


std::vector<test_app::post> test_app::get_author_posts (
    test_app::author& p_author
) {
    std::vector<test_app::post> v_res;
    try {
        pqxx::connection cx(std::getenv("DB_DSN"));
        pqxx::work tx(cx);
        tx.exec("SET SEARCH_PATH TO test_app");
        for (auto [p] : tx.query<test_app::post>("SELECT get_author_posts(p_author := $1)", {p_author})) {
            v_res.emplace_back(p);
        }
        tx.commit();
    } catch (std::exception const &e) {
        std::cerr << e.what() << std::endl;
    }
    return v_res;
}
