# General updates:
# 1. no need to use valid_pg_definition, subclassing a pg type will trigger definition
# flow to be executed on subclass

# Updates on pg_enum, pg_composite, pg_builtin
# There is two interpretations now according to how type inheritance is declared:
# 1. inheriting the type directly treats the type as a new base type
# 2. inheriting a type subtype treats the type as a new domain, check constraints
# need to be merged, comments on the other hand dont

# Updates on pg_sequence
# 1. in order to declare a sequence we need to subclass pg_bigint_sequence, pg_int_sequence
# or pg_smallint_sequence, we cant declare meta types with pg_sequence directly, we cant
# declare subclasses of a pg_sequence subclass
