#include "test_app/types.hpp"


namespace pg = core_pg_bindings;


// "host=172.18.0.1 dbname=mutzhub port=5432 user=mutzhub password=WtbNMMpX46iynzjVobrh8Qu7omvFIL9JEvbkLYYCpCJNIwDWnBwcVquhk6vXe6En"


std::optional<test_app::post> test_app::get_post_by_id (
    pg::int8& p_post_id
) {
    std::optional<test_app::post> v_post;
    try {
        pqxx::connection cx(std::getenv("DB_DSN"));
        pqxx::work tx(cx);
        tx.exec("SET SEARCH_PATH TO test_app");
        std::tuple<std::optional<test_app::post>> response = tx.query1<std::optional<test_app::post>>(
            "SELECT p from post p WHERE id = $1 LIMIT 1",
            {p_post_id}
        );
        tx.commit();
        v_post = std::get<0>(response);
    } catch (std::exception const &e) {
        std::cerr << e.what() << std::endl;
    }
    return v_post;
}


std::optional<std::vector<test_app::comment>> test_app::get_post_comments (
    pg::int8& p_post_id
){
    std::optional<test_app::post> v_post = test_app::get_post_by_id(p_post_id);
    if (v_post.has_value()) {
        return test_app::get_post_comments(v_post.value());
    }
    return std::nullopt;
}


std::vector<test_app::comment> test_app::get_post_comments (
    test_app::post& p_post
){
    std::vector<test_app::comment> v_res;
    try {
        pqxx::connection cx(std::getenv("DB_DSN"));
        pqxx::work tx(cx);
        tx.exec("SET SEARCH_PATH TO test_app");
        for (auto [p] : tx.query<test_app::comment>("SELECT get_post_comments(p_post := $1)", {p_post})) {
            v_res.emplace_back(p);
        }
        tx.commit();
    } catch (std::exception const &e) {
        std::cerr << e.what() << std::endl;
    }
    return v_res;
}


std::optional<test_app::post> test_app::create_post (
    pg::int8& p_author_id, pg::text& p_content, pg::text& p_title
) {
    std::optional<test_app::author> v_author = test_app::get_author_by_id(p_author_id);
    if (!v_author.has_value()) {
        return std::nullopt;
    }
    return test_app::create_post(v_author.value(), p_content, p_title);
}


test_app::post test_app::create_post (
    test_app::author& p_author, pg::text& p_content, pg::text& p_title
) {
    test_app::post v_post;
    pqxx::connection cx(std::getenv("DB_DSN"));
    pqxx::work tx(cx);
    tx.exec("SET SEARCH_PATH TO test_app");
    std::tuple<test_app::post> response = tx.query1<test_app::post>(
        "SELECT create_post(p_author := $1, p_content := $2, p_title := $3)",
        {p_author, p_content, p_title}
    );
    tx.commit();
    return std::get<0>(response);
}


std::optional<test_app::comment> test_app::create_comment (
    pg::int8& p_author_id, pg::int8& p_post_id, pg::text& p_content
) {
    std::optional<test_app::author> v_author = test_app::get_author_by_id(p_author_id);
    std::optional<test_app::post> v_post = test_app::get_post_by_id(p_post_id);
    if (!v_author.has_value() || !v_post.has_value()){
        return std::nullopt;
    }
    return test_app::create_comment(v_author.value(), v_post.value(), p_content);
}


test_app::comment test_app::create_comment (
    test_app::author& p_author, test_app::post& p_post, pg::text& p_content
) {
    test_app::comment v_comment;
    pqxx::connection cx(std::getenv("DB_DSN"));
    pqxx::work tx(cx);
    tx.exec("SET SEARCH_PATH TO test_app");
    std::tuple<test_app::comment> response = tx.query1<test_app::comment>(
        "SELECT create_comment(p_author := $1, p_post := $2, p_content := $3)",
        {p_author, p_post, p_content}
    );
    tx.commit();
    return std::get<0>(response);
}


std::optional<test_app::comment_post> test_app::as_comment_post (
    pg::int8& p_post_id, pg::int8& p_comment_id, pg::text& p_description, pg::int8& p_author_id
) {
    std::optional<test_app::author> v_author = test_app::get_author_by_id(p_author_id);
    std::optional<test_app::post> v_post = test_app::get_post_by_id(p_post_id);
    std::optional<std::vector<test_app::comment>> v_comments = test_app::get_post_comments(p_post_id);
    if (!v_author.has_value() || !v_post.has_value() || (!v_comments.has_value() || (v_comments.has_value() && v_comments.value().size() == 0))){
        return std::nullopt;
    }
    return test_app::as_comment_post(v_post.value(), v_comments.value()[0], p_description, v_author.value());
}


test_app::comment_post test_app::as_comment_post(
    test_app::post& p_post, test_app::comment& p_comment, pg::text& p_description, test_app::author& p_author
) {
    pqxx::connection cx(std::getenv("DB_DSN"));
    pqxx::work tx(cx);
    tx.exec("SET SEARCH_PATH TO test_app");
    std::tuple<test_app::comment_post> response = tx.query1<test_app::comment_post>(
        "SELECT as_comment_post(p_post := $1, p_comment := $2, p_description := $3, p_author := $4)",
        {p_post, p_comment, p_description, p_author}
    );
    tx.commit();
    return std::get<0>(response);
}
