import psycopg
from psycopg import\
    AsyncConnection
from typing import\
    Optional
from psycopg.types import\
    composite as psycomposite,\
    enum as psyenum,\
    TypeInfo
from psycopg.abc import\
    Buffer
from typing import \
    Any,\
    Union
from .definition.common.model import\
    base_model


__all__ = ['adapter_registry']


def _model_as_tuple(
    instance, type_oid: dict[type, int], fields: dict[int, list[str]]
) -> tuple[Any, ...]:
    res = []
    for name in fields[type_oid[instance.__class__]]:
        value = getattr(instance, name)
        if isinstance(value, base_model):
            res.append(_model_as_tuple(value, type_oid, fields))
        else:
            res.append(value)
    return tuple(res)


def _tuple_to_dict(
    cls, type_oid: dict[type, int], fields: dict[int, list[str]],
    oid_field_types: dict[int, list[int]], data: tuple[Any, ...]
) -> dict[str, Any]:
    oid_type: dict[int, type] = {type_oid[k]: k for k in type_oid}
    res: dict[str, Any] = {}
    cls_fields: list[str] = fields[type_oid[cls]]
    cls_field_types: list[int] = oid_field_types[type_oid[cls]]
    for ix in range(0, len(data)):
        field_cls: type = oid_type[cls_field_types[ix]]
        if issubclass(field_cls, base_model):
            res[cls_fields[ix]] = _tuple_to_dict(field_cls, type_oid, fields, oid_field_types, data[ix])
        else:
            res[cls_fields[ix]] = field_cls(data[ix])
    return res


class _BuiltinDumper(psycopg.adapt.Dumper):
    format = psycopg.pq.Format.TEXT

    def dump(self, obj: Any) -> Optional[Union[bytes, bytearray, memoryview]]:
        return str(obj).encode()


class _BuiltinLoader(psycopg.adapt.Loader):
    def load(self, data: Union[bytes, bytearray, memoryview]) -> Any:
        return self.__class__.base_type(data.decode('utf-8'))


class _RecordLoader(psycomposite.CompositeLoader):
    def _load_recursive(self, data: Buffer, field_types: list[int]) -> None:
        if data == b"()":
            return ()
        res = []
        for token in self._parse_record(data[1:-1]):
            types = field_types[1:]
            if token is None:
                continue
            if token[0] == 40 and token[-1] == 41 and types[0] != self.text_oid:
                # '(' and ')'
                res.append(self._load_recursive(token, types))
            else:
                res.append(token.decode('utf-8'))
        return tuple(res)

    def load(self, data: Buffer) -> tuple[Any, ...]:
        # cast = self._tx.get_loader(TEXT_OID, self.format).load
        # return tuple(
        #     cast(token) if token is not None else None
        #     for token in self._parse_record(data[1:-1])
        # )
        return self._load_recursive(data, self.field_types)


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

    def register_composite(self, cls: type, schema: str, name: str) -> None:
        info = psycomposite.CompositeInfo.fetch(self._conn, f'{schema}.{name}')
        self._oid_fields[info.oid] = info.field_names
        self._oid_field_types[info.oid] = info.field_types
        oid_fields = self._oid_fields
        type_oid = self._type_oid
        oid_field_types = self._oid_field_types
        type_oid = self._type_oid
        dumper: type = type(f'{schema}_{name}_Dumper', (psycomposite.TupleDumper, ),
                            {'dump': lambda self, obj: psycomposite.TupleDumper.dump(self,   _model_as_tuple(obj, type_oid, oid_fields)),
                            'oid': info.oid})
        # consider using model_construct instead of cls constructor, this way validations
        # are not run
        loader: type = type(f'{schema}_{name}_Loader', (_RecordLoader, ),
                            {'load': lambda self, data: cls(**_tuple_to_dict(cls, type_oid, oid_fields, oid_field_types, _RecordLoader.load(self, data))),
                            'field_types': list(oid_field_types[info.oid]),
                            'text_oid': psycopg.adapters.types.get_oid('text')})
        psycopg.adapters.register_dumper(cls, dumper)
        psycopg.adapters.register_loader(dumper.oid, loader)
        self._type_oid[cls] = info.oid

    def register_enum(self, cls: type, schema: str, name: str) -> None:
        info = psyenum.EnumInfo.fetch(self._conn, f'{schema}.{name}')
        self._type_oid[cls] = info.oid
        psyenum.register_enum(info, None, cls)

    def register_type(self, cls: type, schema: str, name: str) -> None:
        if schema == 'pg_catalog':
            info = TypeInfo.fetch(self._conn, name)
        else:
            info = TypeInfo.fetch(self._conn, f'{schema}.{name}')
        self._type_oid[cls] = info.oid
        loader: type = type(f'{schema}_{name}_Loader', (_BuiltinLoader, ),
                            {'base_type': cls})
        dumper: type = type(f'{schema}_{name}_Dumper', (_BuiltinDumper, ),
                            {'oid': info.oid})
        psycopg.adapters.register_dumper(cls, dumper)
        psycopg.adapters.register_loader(dumper.oid, loader)
        self._type_oid[cls] = info.oid


adapter_registry = AdapterRegistry()
