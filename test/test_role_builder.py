# import pg_definition.builder.role as rb
# import psycopg
# from typing import\
#     Generator
# import sys
# sys.path.append('.')
# import test_app as ta
# import test_app.backend as test_app
# 
# 
# dsn_test_db: str = 'host=172.18.0.1 dbname=mutzhub port=5432 user=mutzhub password=WtbNMMpX46iynzjVobrh8Qu7omvFIL9JEvbkLYYCpCJNIwDWnBwcVquhk6vXe6En'
# 
# 
# def double_inclusion(builder: rb.Builder, sentences: list[str]) -> None:
#     builder_sentences: list[str] = []
#     with psycopg.connect(dsn_test_db) as conn:
#         for bs in builder:
#             sentence, identifiers, params = bs.sql_sentence_params()
#             sentence_sql = psycopg.sql.SQL(sentence).format(*identifiers).as_string(conn)
#             print(sentence_sql, params)
#             builder_sentences.append(sentence_sql)
#     print(builder_sentences)
#     assert(len(builder_sentences) == len(sentences))
#     assert all([bs in sentences for bs in builder_sentences])
#     assert all([s in builder_sentences for s in sentences])
# 
# 
# def test_role_builder_on_executes_correctly_on_permissions() -> None:
#     def mod_generator_1() -> Generator[rb.SQLSentenceParams, None, None]:
#         yield from rb.builder(test_app.roles.test_schema_usage).create()\
#             .schema(ta.test).usage().grant()\
#             .schema(ta.test).create().revoke()
# 
#     double_inclusion(mod_generator_1(), [
#         'CREATE ROLE "test_schema_usage"',
#         'GRANT USAGE ON SCHEMA "test" TO "test_schema_usage"',
#         'REVOKE CREATE ON SCHEMA "test" FROM "test_schema_usage"'])
# 
#     def mod_generator_2() -> Generator[rb.SQLSentenceParams, None, None]:
#         yield from rb.builder(test_app.roles.comment_consultation).create()\
#             .table(ta.test.comment).select().grant()\
#             .table(ta.test.comment).references().grant()\
#             .table(ta.test.comment).update().revoke()\
#             .table(ta.test.comment).delete().revoke()\
#             .table(ta.test.comment).insert().revoke()
# 
#     double_inclusion(mod_generator_2(), [
#         'CREATE ROLE "comment_consultation"',
#         'GRANT SELECT ON TABLE "test"."comment" TO "comment_consultation"',
#         'GRANT REFERENCES ("id") ON "test"."comment" TO "comment_consultation"',
#         'REVOKE UPDATE ON TABLE "test"."comment" FROM "comment_consultation"',
#         'REVOKE DELETE ON TABLE "test"."comment" FROM "comment_consultation"',
#         'REVOKE INSERT ON TABLE "test"."comment" FROM "comment_consultation"'])
# 
#     def mod_generator_3() -> Generator[rb.SQLSentenceParams, None, None]:
#         yield from rb.builder(test_app.roles.comment_creation).create()\
#             .table(ta.test.comment).insert().grant()\
#             .sequence(ta.test.comment_id_sequence).usage().grant()\
#             .sequence(ta.test.comment_id_sequence).update().grant()\
#             .function(ta.test.create_comment).execute().grant()
# 
#     double_inclusion(mod_generator_3(), [
#         'CREATE ROLE "comment_creation"',
#         'GRANT INSERT ON TABLE "test"."comment" TO "comment_creation"',
#         'GRANT USAGE ON SEQUENCE "test"."comment_id_sequence" TO "comment_creation"',
#         'GRANT UPDATE ON SEQUENCE "test"."comment_id_sequence" TO "comment_creation"',
#         'GRANT EXECUTE ON FUNCTION "test"."create_comment" TO "comment_creation"'])
# 
# 
# def test_role_builder_on_executes_correctly_on_roles() -> None:
# 
#     def mod_generator_1() -> Generator[rb.SQLSentenceParams, None, None]:
#         yield from rb.builder(test_app.roles.poster).create()\
#             .permission(test_app.roles.post_consultation).grant()\
#             .permission(test_app.roles.post_creation).grant()\
#             .permission(test_app.roles.author_consultation).grant()\
#             .permission(test_app.roles.comment_creation).revoke()
# 
#     double_inclusion(mod_generator_1(), [
#         'CREATE ROLE "poster"',
#         'GRANT "post_consultation" TO "poster"',
#         'GRANT "post_creation" TO "poster"',
#         'GRANT "author_consultation" TO "poster"',
#         'REVOKE "comment_creation" FROM "poster"'])
# 
# 
# def test_role_builder_detects_invalid_definitions() -> None:
# 
#     try:
#         rb.builder(test_app.roles.poster).create()\
#             .schema(ta.test).usage().grant()
#     except AttributeError as e:
#         assert str(e) == "'RoleBuilder' object has no attribute 'schema'"
# 
#     try:
#         rb.builder(test_app.roles.comment_creation).create()\
#             .table(ta.test.comment).insert().grant()\
#             .schema(ta.test).usage().grant()
#     except TypeError as e:
#         assert str(e) == 'Error definition_value_is_present: "usage" must be present in "comment_creation" definition grants over "test"'
# 
# 
# test_role_builder_detects_invalid_definitions()
# 
