import os
from parse import\
    parse
from typing import\
    Optional
import argparse
import sys
import importlib


# NOTE: dsn will come through extension config file
# if the extension uses pgdrivers migrations then it 
# must add a section from which pgdriver will read the extension configuration.
# NOTE: the script will receive the parameter 'with_datafix' through the 
# arguments when invoked. by now its hardcoded.
# NOTE: The destination path for migrations must also be included in the 
# pgdriver migration section in configuration file, for now its hardcoded
def check_datafix_not_bound_to_migrations(datafix_id: int, dest_path: str) -> None:
    sys.path.append(dest_path)
    for mgr_path in os.listdir(dest_path):
        if mgr_path.startswith('__'):
            continue
        mgr = importlib.import_module(mgr_path[:-3])
        mgr_id = getattr(mgr, "MIGRATION_ID")
        if getattr(mgr, 'DATAFIX_ID') == datafix_id:
            raise Exception(f'Datafix "{datafix_id}" is already bound to migration "{mgr_id}"')


def check_migration_exists(migration_id: int, dest_path: str) -> None:
    assert os.path.exists(f'{dest_path}/migration_{migration_id}.py')
    sys.path.append(dest_path)
    mgr = importlib.import_module(f'migration_{migration_id}')
    assert getattr(mgr, "MIGRATION_ID") == migration_id


def determine_last_generated_id(path: str, parse_name: str) -> Optional[int]:
    last_migration: Optional[int] = None
    for migration_name in os.listdir(path):
        if migration_name.startswith('__'):
            continue
        try:
            mgr = int(parse(parse_name, migration_name)[0])
            if last_migration is None or mgr > last_migration:
                last_migration = mgr
        except Exception as e:
            raise Exception(e)
    return last_migration


def generate_migration(
    migration_id: int, datafix_id: Optional[int], dest_path: str,
    depends_on: Optional[int], template_path: str
) -> int:
    """
    The migration is presumed to apply changes on the extensions database objects, tables and
    so on. these changes must be reflected in the pg objects defined by the extension.
    """
    if not os.path.exists(dest_path):
        os.mkdir(dest_path)

    mgr_name: str = f'migration_{migration_id}'
    mgr_path: str = f'{dest_path}/{mgr_name}.py'

    if os.path.exists(mgr_path):
        print(f'There is already a migration with name "{mgr_name}.py" at destination path "{dest_path}"')
        exit(1)

    mgr_template: str = ''
    with open(f'{template_path}/migration.tpl', 'r') as mgrtpl:
        mgr_template = mgrtpl.read()

    with open(mgr_path, 'w') as mgrdest:
        mgrdest.write(mgr_template
                      .format(migration_id=migration_id, depends_on=depends_on,
                              datafix_id=datafix_id))


def generate_datafix(
    datafix_id: int, dest_path: str, template_path: str
) -> int:
    """
    The migration is presumed to apply changes on the extensions database objects, tables and
    so on. these changes must be reflected in the pg objects defined by the extension.
    """
    if not os.path.exists(dest_path):
        os.mkdir(dest_path)

    df_name: str = f'datafix_{datafix_id}'
    df_path: str = f'{dest_path}/{df_name}.sql'

    if os.path.exists(f'{dest_path}/{df_name}.sql'):
        print(f'There is already a datafix with name "{df_name}.sql" at destination path "{dest_path}"')
        exit(1)

    df_template: str = ''
    with open(f'{template_path}/datafix.tpl', 'r') as dftpl:
        df_template = dftpl.read()

    with open(df_path, 'w') as dfdest:
        dfdest.write(df_template
                     .format(datafix_id=datafix_id))


if __name__ == '__main__':
    # will have to look in the package installation directory to see these paths. Each extension package will have its own migration directory
    package_install_path: str = '/home/smora/sgs/dev/pgdriver/pgdriver'
    mgr_dest_path: str = f'{package_install_path}/var/migration'
    df_dest_path: str = f'{package_install_path}/var/datafix'
    # template will be a part of pgdriver base package
    template_path: str = '/home/smora/sgs/dev/pgdriver/pgdriver/migration/template'

    parser = argparse.ArgumentParser(
        prog='Migration Generator',
        description='Generates database migrations for ordered database changes and datafixes',
        epilog='')

    group_exc = parser.add_mutually_exclusive_group(required=True)
    group_exc.add_argument('--datafix', help='Generate a datafix file', action='store_true')
    group_exc.add_argument('--migration', help='Generate a migration file', action='store_true')

    mgr_group = parser.add_argument_group('Migration Options')
    mgr_group_exc = mgr_group.add_mutually_exclusive_group()
    mgr_group_exc.add_argument('--bind-datafix-id', type=int, help='Bind with existing datafix')
    mgr_group_exc.add_argument('--with-datafix', help='Generate migration, datafix and bind with them together', action='store_true')
    mgr_group.add_argument('--depends-on', type=int, help='Indicate an existing migration id that this migration depends on')

    df_group = parser.add_argument_group('Datafix Options')

    args = parser.parse_args(sys.argv[1:])

    if args.migration:
        last_migration_id: Optional[int] = determine_last_generated_id(mgr_dest_path, 'migration_{}.py')
        migration_id: int = 1 if last_migration_id is None else last_migration_id + 1
        if args.depends_on is not None:
            check_migration_exists(args.depends_on, mgr_dest_path)
        if args.bind_datafix_id is not None:
            # check that datafix exists
            assert os.path.exists(f'{df_dest_path}/datafix_{args.bind_datafix_id}.sql')
            # check that the datafix is not related to any other migration
            check_datafix_not_bound_to_migrations(args.bind_datafix_id, mgr_dest_path)
            print(f'Generating migration #{migration_id} bound to datafix #{args.bind_datafix_id}...')
            # check depends_on migration exists
            generate_migration(migration_id, args.bind_datafix_id, mgr_dest_path, args.depends_on, template_path)
        elif args.with_datafix:
            last_datafix_id: Optional[int] = determine_last_generated_id(df_dest_path, 'datafix_{}.sql')
            datafix_id: int = 1 if last_datafix_id is None else last_datafix_id + 1
            print(f'Generating migration #{migration_id} and datafix #{datafix_id}...')
            generate_datafix(datafix_id, df_dest_path, template_path)
            # check depends_on migration exists
            generate_migration(migration_id, datafix_id, mgr_dest_path, args.depends_on, template_path)
        else:
            print(f'Generating migration #{migration_id}...')
            generate_migration(migration_id, None, mgr_dest_path, args.depends_on, template_path)
    elif args.datafix:
        last_datafix_id: Optional[int] = determine_last_generated_id(df_dest_path, 'datafix_{}.sql')
        print('Generating datafix, --bind-datafix-id, --with-datafix, --depends-on switches will be ignored.')
        datafix_id: int = 1 if last_datafix_id is None else last_datafix_id + 1
        print(f'Generating datafix #{datafix_id}...')
        generate_datafix(datafix_id, df_dest_path, template_path)
