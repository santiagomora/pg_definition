from datetime import\
    time
from typing import\
    TYPE_CHECKING,\
    Any,\
    Type,\
    Optional,\
    Iterator,\
    Callable
from typing_extensions import\
    Annotated
from pydantic_core import\
    core_schema
from pydantic.annotated_handlers import\
    GetCoreSchemaHandler
from pydantic.types import\
    _check_annotated_type
from pydantic import\
    BaseModel
from pydantic.fields import\
    FieldInfo
from dataclasses import\
    dataclass
from abc import\
    ABC,\
    abstractmethod
# parece que pydantic no incluye los types NaiveTime, AwareTime, PastTime o 
# FutureTime. unicamente soporta de datetime, tomamos el codigo fuente
# e hicimos las extensiones que parecian necesarias
if TYPE_CHECKING:
    _AwareTime = Annotated[time, ...]
    _NaiveTime = Annotated[time, ...]
    # PastDatetime = Annotated[time, ...]
    # FutureDatetime = Annotated[time, ...]

else:
    class _AwareTime:
        """A datetime that requires timezone info."""

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.time_schema(tz_constraint='aware')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'time', cls.__name__)
                schema['tz_constraint'] = 'aware'
                return schema

        def __repr__(self) -> str:
            return 'AwareTime'

    class _NaiveTime:
        """A datetime that doesn't require timezone info."""

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.time_schema(tz_constraint='naive')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'time', cls.__name__)
                schema['tz_constraint'] = 'naive'
                return schema

        def __repr__(self) -> str:
            return 'NaiveTime'


    # es schema de time no soporta now_op
    # class PastTime:
    #     """A datetime that must be in the past."""
    # 
    #     @classmethod
    #     def __get_pydantic_core_schema__(
    #         cls, source: type[Any], handler: GetCoreSchemaHandler
    #     ) -> core_schema.CoreSchema:
    #         if cls is source:
    #             # used directly as a type
    #             return core_schema.time_schema(now_op='past')
    #         else:
    #             schema = handler(source)
    #             _check_annotated_type(schema['type'], 'time', cls.__name__)
    #             schema['now_op'] = 'past'
    #             return schema
    # 
    #     def __repr__(self) -> str:
    #         return 'PastTime'
    # 
    # class FutureTime:
    #     """A datetime that must be in the future."""
    # 
    #     @classmethod
    #     def __get_pydantic_core_schema__(
    #         cls, source: type[Any], handler: GetCoreSchemaHandler
    #     ) -> core_schema.CoreSchema:
    #         if cls is source:
    #             # used directly as a type
    #             return core_schema.time_schema(now_op='future')
    #         else:
    #             schema = handler(source)
    #             _check_annotated_type(schema['type'], 'time', cls.__name__)
    #             schema['now_op'] = 'future'
    #             return schema
    # 
    #     def __repr__(self) -> str:
    #         return 'FutureTime'
@dataclass
class FieldData:
    name: str
    info: FieldInfo


class Metadata(ABC):
    _annotated: Optional[FieldData] = None

    def set_annotated(self, data: FieldData):
        self._annotated = data


# es metadata asociada a definiciones de postgres y que sera analizada
# por la herramienta
class PGMetadata(Metadata, ABC):
    @staticmethod
    @abstractmethod
    def get_aggregation_lambdas() -> dict[str, Callable[[Any], str]]:
        pass

    @abstractmethod
    def to_description_dict(self) -> dict[str, Any]:
        pass


class PGBaseModel(BaseModel):
    @classmethod
    def get_metadata(cls) -> Iterator[tuple[str, Metadata]]:
        for name, info in cls.model_fields.items():
            field_data = FieldData(name, info)
            for meta in info.metadata:
                yield (field_data, meta, )

    # @classmethod
    # def __get_pydantic_core_schema__(
    #     cls,
    #     source: Type[Any],
    #     handler: GetCoreSchemaHandler
    # ) -> core_schema.CoreSchema:
    #     # queria un metodo que pudiera ejecutarse antes de la obtencion del schema
    #     # pero este es el unico hook que encontre, capaz cuando me familiarice un poco
    #     # mas con los docs encuentre otro
    #     for field_data, meta in cls.get_metadata():
    #         if isinstance(meta, Metadata):
    #             meta.set_annotated(field_data)
    #         else:
    #             # printear que la definicion no es instancia de metadata
    #             # print(f'WARNING: annotation {meta!r} is not a Metadata instance.')
    #             pass
    #     return super().__get_pydantic_core_schema__(source, handler)

