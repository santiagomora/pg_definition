# from .db.schema import\
#     schema
# # from ._adapter_registry import\
# #     AdapterRegistry
# import base_types as bt
# from .types.builtin import builtin
# 
# 
# class pg_catalog(schema):
#     class int2(bt.int2, metaclass=builtin):
#         pass
# 
#     class int4(bt.int4, metaclass=builtin):
#         pass
# 
#     class int8(bt.int8, metaclass=builtin):
#         pass
# 
#     class float4(bt.float4, metaclass=builtin):
#         pass
# 
#     class float8(bt.float8, metaclass=builtin):
#         pass
# 
#     class char(bt.int1, metaclass=builtin):
#         pass
# 
#     class bool(bt.bool, metaclass=builtin):
#         pass
# 
#     class text(bt.text, metaclass=builtin):
#         pass
# 
#     class timestamptz(bt.timestamptz, metaclass=builtin):
#         pass
# 
#     class date(bt.date, metaclass=builtin):
#         pass
# 
#     # class timetz(bt.timetz, metaclass=builtin):
#     #     pass
# 
# 
# 
# def register_types(ar: AdapterRegistry):
#     ar.register_type(pg_catalog.int4)
#     ar.register_type(pg_catalog.int8)
#     ar.register_type(pg_catalog.int2)
#     ar.register_type(pg_catalog.float4)
#     ar.register_type(pg_catalog.text)
#     ar.register_type(pg_catalog.char, '"char"')
#     ar.register_type(pg_catalog.float8)
#     ar.register_type(pg_catalog.bytea)
#     ar.register_type(pg_catalog.timestamptz)
#     # ar.register_type(pg_catalog.timetz)
#     ar.register_type(pg_catalog.date)
#     ar.register_type(pg_catalog.bool)
