# +-----------+
# | MIGRATION |
# +-----------+
# -
# Diseno de alto nivel
# -
# cada modulo puede decidir si usar las migraciones de pgdriver
# con lo cual debe existir:
# 1. un mecanismo para instalar las tablas de migraciones en el schema del modulo (hook install de script de setup)
# -
# 2. un mecanismo para exponer los types a los cuales se le dara seguimiento
# -
# 3. un mecanismo para detectar los cambios en ellos y aplicarlos en la base de datos. aqui 
# el movimiento es unidireccional, es decir los types nuevos recibidos siempre pisaran los
# cambios de la base de datos. la idea es no definir types por fuera de la base de datos
# -
# 4. un mecanismo para eliminar los types del modulo de la base de datos y las tablas de migraciones (hook uninstall de setup)
# -
# 5. los mecanismos de 1 y 4 deben poder correrse libremente (?)

# -
# FUNCIONAMIENTO INTERNO
# -
# El modulo de migraciones en principio se encargara del seguimiento de los types unicamente.
# Utilizara las definiciones extraidas al aplicar alos types el definition flow del registro, 
# es decir con el decorador valid_pg_definition.

# -
# ESTRUCTURA
# -
# la idea es tener trazabilidad de los cambios en los types del modulo
# -

# tabla mgr_migration
# campos propuestos:
# id serial (pk)
# date timestamptz
# operation (enums con operaciones disponibles migrate/rollback, etc)

# tabla mgr_object
# campos propuestos:
# id serial (pk)
# oid (unique) (?)
# schema text
# name text
# unique (schema, name)

# tabla mgr_table_object(mgr_object)
# tabla mgr_enums_object(mgr_object)
# tabla mgr_composite_object(mgr_object)
# tabla mgr_domain_object(mgr_object)

# tabla mgr_attribute
# id serial bigint (pk)
# name text

# tabla mgr_object_attribute
# attribute_id bigint (fk to mgr_attribute)
# object_id (fk to mgr_object)


# tabla mgr_object_changelog
# campos propuestos:
# migration_id bigint (fk to mgr_migration)
# object_id bigint (fk to mgr_object)
# change_operation (enums create/delete/modify)
# attribute_id bigint (fk to mgr_attribute)
# pk(migration_id, object_id, change_operation, attribute_id)


# tabla mgr_table_changelog(mgr_object_changelog)
# tabla mgr_enums_changelog(mgr_object_changelog)
# tabla mgr_composite_changelog(mgr_object_changelog)
# tabla mgr_domain_changelog(mgr_object_changelog)


# tabla mgr_table_foreign_key(mgr_attribute)
# tabla mgr_table_index(mgr_attribute)
# tabla mgr_table_primary_key(mgr_attribute)
# tabla mgr_table_unique_index(mgr_attribute)
# tabla mgr_table_column(mgr_attribute)

# tabla mgr_enums_value(mgr_attribute)
# tabla mgr_enums_comment(mgr_attribute)
# tabla mgr_domain_check_constraint(mgr_attribute)
# tabla mgr_domain_comment(mgr_attribute)
# tabla mgr_composite_attribute(mgr_attribute)
# tabla mgr_composite_check_constraint(mgr_attribute)
# tabla mgr_composite_comment(mgr_attribute)


# +--------+
# | SCRIPT |
# +--------+
# es un mecanismo para agregar scripts para que se ejecuten al momento de correr la migracion 
# podemos proporcionar alguna manera de correr antes/despues de la migracion


# +------+
# | LINK |
# +------+
# El modulo no solo provee el mecanismo para seguimiento de types, sino tambien una libreria
# para usar la base de datos a traves de C++ con pybind11. Es decir este paquete sera compilado
# y proveera mecanismos para pooling de conexiones y la libreria para acceder a la base de datos
# q luego otros modulos podran usar desde lo q sea q expongan con C++

