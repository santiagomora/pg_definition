from ..connection.handler import\
    PGConnectionHandler
from psycopg.types.composite import\
    CompositeInfo,\
    register_composite
from psycopg.types.enum import\
    EnumInfo,\
    register_enum
from psycopg.types import\
    TypeInfo
from .base import\
    pg_class,\
    pg_type,\
    pg_enum
from psycopg.adapt import\
    Loader,\
    Dumper
from psycopg import\
    adapters
from typing import\
    Optional


class PGTypeDescriptor:
    class Info:
        def __init__(self, dispatcher: PGConnectionHandler.Dispatcher) -> None:
            self._dispatcher = dispatcher

        async def get_composite_info(self, schema: str, name: str) -> Optional[CompositeInfo]:
            async with self._dispatcher.cursor([schema]) as cursor:
                return await CompositeInfo.fetch(cursor._cursor.connection, f'{schema}.{name}')

        async def get_type_info(self, schema: str, name: str) -> Optional[TypeInfo]:
            async with self._dispatcher.cursor([schema]) as cursor:
                return await TypeInfo.fetch(cursor._cursor.connection, f'{schema}.{name}')

        async def get_enum_info(self, schema: str, name: str) -> Optional[EnumInfo]:
            async with self._dispatcher.cursor([schema]) as cursor:
                return await EnumInfo.fetch(cursor._cursor.connection, f'{schema}.{name}')

    def __init__(self, info: Info):
        self._ta = info

    async def register_composite(self, schema: str, name: str, cls: type[pg_class]) -> None:
        info: Optional[CompositeInfo] = await self._ta.get_composite_info(schema, name)
        if info is None:
            # el type no existe, hay que correr los script de migracion
            raise Exception
        cls.set_info(info)
        register_composite(info)

    async def register_enum(self, schema: str, name: str, cls: type[pg_enum]) -> None:
        info: Optional[EnumInfo] = await self._ta.get_enum_info(schema, name)
        if info is None:
            # el type no existe, hay que correr los script de migracion
            raise Exception
        register_enum(info)

    async def register_loader(self, schema: str, name: str, loader: type[Loader]) -> None:
        info: Optional[TypeInfo] = await self._ta.get_type_info(schema, name)
        if info is None:
            raise Exception
        adapters.register_loader(info.oid, loader)

    async def register_dumper(self, cls: type[pg_type], dumper: type[Dumper]) -> None:
        adapters.register_dumper(cls, dumper)
