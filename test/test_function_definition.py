# import psycopg
# from pgdriver import\
#     pg_single_result_function,\
#     pg_set_returning_function,\
#     pg_execute_function,\
#     table,\
#     bigint,\
#     timestamp,\
#     text,\
#     bigint_sequence,\
#     default_nextval
# from pgdriver.definition.definition.table import\
#     table_primary_key,\
#     table_foreign_key
# from typing import\
#     Optional,\
#     Any
# from typing_extensions import \
#     Annotated
# import json
# 
# 
# dsn_test_db: str = 'host=172.18.0.1 dbname=mutzhub port=5432 user=mutzhub password=WtbNMMpX46iynzjVobrh8Qu7omvFIL9JEvbkLYYCpCJNIwDWnBwcVquhk6vXe6En'
# 
# 
# class author_id_sequence(bigint_sequence):
#     pass
# 
# 
# class post_id_sequence(bigint_sequence):
#     pass
# 
# 
# class comment_id_sequence(bigint_sequence):
#     pass
# 
# 
# class author(table):
#     id: Annotated[bigint, table_primary_key(name='post_pk'),
#                   default_nextval(seq=author_id_sequence)]
#     name: text
# 
# 
# class with_timestamps(table):
#     created_at: timestamp
#     updated_at: timestamp
# 
# 
# class authored(table):
#     author_id: Annotated[bigint, table_foreign_key(name='authorable_author_fk',
#                                                          other_class=author,
#                                                          other_class_column_name='id')]
#     content: text
# 
# 
# class post(authored, with_timestamps):
#     id: Annotated[bigint, table_primary_key(name='post_pk'),
#                   default_nextval(seq=post_id_sequence)]
#     title: text
# 
# 
# class comment(authored, with_timestamps):
#     id: Annotated[bigint, table_primary_key(name='comment_pk')]
#     post_id: Annotated[bigint, table_foreign_key(name='comment_post_fk',
#                                                        other_class=post,
#                                                        other_class_column_name='id'),
#                        default_nextval(seq=comment_id_sequence)]
# 
# 
# class get_post_by_id(pg_single_result_function[post]):
#     pass
# 
# 
# class get_post_comments(pg_set_returning_function[comment]):
#     pass
# 
# 
# class create_post(pg_single_result_function[comment]):
#     pass
# 
# 
# class create_comment(pg_single_result_function[comment]):
#     pass
# 
# 
# class TableTypeLoader(psycopg.abc.Loader):
#     
# 
# 
# def test_sql_function_gets_parameters_correctly() -> None:
#     # NOTE test that function store post correctly
#     extension_description: Optional[dict[str, Any]] = None
#     with open('./test/sql/extension.json', 'r') as f:
#         extension_description = json.load(f)
#     
#     # with psycopg.connect(dsn_test_db) as conn:
#         # print(conn)
# 
# 
# test_sql_function_gets_parameters_correctly()
# 
# 
