import psycopg
from psycopg import\
    AsyncConnection
from typing import\
    Optional
from psycopg.types import\
    composite as psycomposite,\
    enum as psyenum,\
    TypeInfo
import functools
from psycopg.abc import\
    Buffer
from typing import \
    Any,\
    Union


__all__ = ['adapter_registry']


class _BuiltinDumper(psycopg.adapt.Dumper):
    format = psycopg.pq.Format.TEXT

    def dump(self, obj: Any) -> Optional[Union[bytes, bytearray, memoryview]]:
        return str(obj).encode()


class _BuiltinLoader(psycopg.adapt.Loader):
    def load(self, data: Union[bytes, bytearray, memoryview]) -> Any:
        return self.__class__.base_type(data)


class _RecordLoader(psycomposite.BaseCompositeLoader):
    def _load_recursive(self, data: Buffer) -> None:
        if data == b"()":
            return ()
        res = []
        for token in self._parse_record(data[1:-1]):
            if token is None:
                continue
            if token[0] == 40 and token[-1] == 41:
                # '(' and ')'
                res.append(self._load_recursive(token))
            else:
                res.append(token.decode('utf-8'))
        return tuple(res)

    def load(self, data: Buffer) -> tuple[Any, ...]:
        # cast = self._tx.get_loader(TEXT_OID, self.format).load
        # return tuple(
        #     cast(token) if token is not None else None
        #     for token in self._parse_record(data[1:-1])
        # )
        return self._load_recursive(data)


class AdapterRegistry:
    def __init__(self) -> None:
        self._type_oid: dict[type, int] = {}
        self._oid_fields: dict[int, list[str]] = {}
        self._oid_field_types: dict[int, list[int]] = {}
        self._conn: Optional[AsyncConnection] = None
        self._dsn: Optional[str] = None

    def __call__(self, dsn: str):
        assert self._dsn is None
        assert self._conn is None
        self._dsn = dsn
        return self

    def __enter__(self):
        self._conn = psycopg.connect(self._dsn)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._conn.close()
        self._conn = None
        self._dsn = None

    def configure_adapters(self, cls, dumper: type, loader: type) -> None:
        psycopg.adapters.register_dumper(cls, dumper)
        psycopg.adapters.register_loader(dumper.oid, loader)
        self._type_oid[cls] = dumper.oid

    @functools.cache
    def _store_composite_info(self, cls: type, schema: str, name: str) -> int:
        info = psycomposite.CompositeInfo.fetch(self._conn, f'{schema}.{name}')
        self._oid_fields[info.oid] = info.field_names
        self._oid_field_types[info.oid] = info.field_types
        return info.oid

    @functools.cache
    def _store_enum_info(self, cls: type, schema: str, name: str) -> int:
        info = psyenum.EnumInfo.fetch(self._conn, f'{schema}.{name}')
        self._type_oid[cls] = info.oid
        psyenum.register_enum(info, None, cls)
        return info.oid

    @functools.cache
    def _store_type_info(self, cls: type, schema: str, name: str) -> int:
        if schema == 'pg_catalog':
            info = TypeInfo.fetch(self._conn, name)
        else:
            info = TypeInfo.fetch(self._conn, f'{schema}.{name}')
        self._type_oid[cls] = info.oid
        return info.oid

    def _generate_composite_dumper(self, cls: type, schema: str, name: str) -> type:
        oid = self._store_composite_info(cls, schema, name)
        oid_fields = self._oid_fields
        type_oid = self._type_oid
        return type(f'{schema}_{name}_Dumper',
                    (psycomposite.TupleDumper, ),
                    {'dump': lambda self, obj: psycomposite.TupleDumper.dump(self, obj.as_tuple(type_oid, oid_fields)),
                     'oid': oid})

    def _generate_composite_loader(self, cls: type, schema: str, name: str) -> tuple[int, type]:
        self._store_composite_info(cls, schema, name)
        oid_fields = self._oid_fields
        oid_field_types = self._oid_field_types
        type_oid = self._type_oid
        return type(f'{schema}_{name}_Loader', (_RecordLoader, ),
                    {'load': lambda self, data: cls(**cls.from_tuple(type_oid, oid_fields, oid_field_types, _RecordLoader.load(self, data)))})

    def _generate_type_dumper(self, cls: type, schema: str, name: str) -> type:
        oid = self._store_type_info(cls, schema, name)
        return type(f'{schema}_{name}_Dumper',
                    (_BuiltinDumper, ),
                    {'oid': oid})

    def _generate_type_loader(self, cls: type, schema: str, name: str) -> tuple[int, type]:
        self._store_type_info(cls, schema, name)
        return type(f'{schema}_{name}_Loader', (_BuiltinLoader, ),
                    {'base_type': cls})

    def configure_composite(self, cls: type, schema: str, name: str) -> None:
        dumper = self._generate_composite_dumper(cls, schema, name)
        loader = self._generate_composite_loader(cls, schema, name)
        self.configure_adapters(cls, dumper, loader)

    def configure_enum(self, cls: type, schema: str, name: str) -> None:
        self._store_enum_info(cls, schema, name)

    def configure_type(self, cls: type, schema: str, name: str) -> None:
        dumper = self._generate_type_dumper(cls, schema, name)
        loader = self._generate_type_loader(cls, schema, name)
        self.configure_adapters(cls, dumper, loader)


adapter_registry = AdapterRegistry()
