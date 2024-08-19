# 
# @in_pg_schema('public')
# class pg_past_date(date,
#                    metaclass=_with_schema_metaclass(core_schema.date_schema(strict=True,
#                                                                             now_op="past"))):
#     pass
# 
# 
# @in_pg_schema('public')
# class pg_future_date(date,
#                      metaclass=_with_schema_metaclass(core_schema.date_schema(strict=True,
#                                                                               now_op="future"))):
#     pass
# 
# 
# @in_pg_schema('public')
# class pg_past_timetstampz(datetime,
#                           metaclass=_with_schema_metaclass(core_schema.datetime_schema(strict=True,
#                                                                                        tz_constraint='aware',
#                                                                                        now_op="past"))):
#     pass
# 
# 
# @in_pg_schema('public')
# class pg_future_timestamptz(datetime,
#                             metaclass=_with_schema_metaclass(core_schema.datetime_schema(strict=True,
#                                                                                          tz_constraint='aware',
#                                                                                          now_op="future"))):
#     pass
# 
# 
# 
# @in_pg_schema('public')
# class pg_past_timestamp(datetime,
#                         metaclass=_with_schema_metaclass(core_schema.datetime_schema(strict=True,
#                                                                                      tz_constraint='naive',
#                                                                                      now_op="past"))):
#     pass
# 
# 
# @in_pg_schema('public')
# class pg_future_timestamp(datetime,
#                           metaclass=_with_schema_metaclass(core_schema.datetime_schema(strict=True,
#                                                                                        tz_constraint='naive',
#                                                                                        now_op="future"))):
#     pass
