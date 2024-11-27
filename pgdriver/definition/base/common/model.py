from .flow import\
    RootDefinitionFlowNode,\
    execute_definition_flow,\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator,\
    FlowNodeException
from pydantic import\
    BaseModel,\
    ConfigDict
from pydantic.fields import\
    FieldInfo
from ...inspection import\
    get_field_classified_metadata_appearances,\
    extract_definition_fields,\
    extract_type
from typing import\
    Any


pg_composite_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('composite-definition-flow')
pg_table_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('table-definition-flow')


class _PGBaseModelMeta(type(BaseModel)):
    def __new__(cls, clsname, clsbases, namespace, **kwargs) -> type[BaseModel]:

        rettype: type[BaseModel] = super()\
            .__new__(cls, clsname, clsbases, namespace, **(kwargs))

        try:
            if issubclass(rettype, pg_table):
                execute_definition_flow(rettype, pg_table_definition_flow_root)
            elif issubclass(rettype, pg_composite):
                execute_definition_flow(rettype, pg_composite_definition_flow_root)
        except NameError:
            pass
        return rettype


class _PGBaseModel(BaseModel, metaclass=_PGBaseModelMeta):
    def __init__(self, **data: Any) -> None:
        for parent_cls in reversed(self.__class__.mro()[1:-4]):
            parent_cls.__pydantic_validator__.validate_python(data, self_instance=self)
        return super().__init__(**data)


class pg_composite(_PGBaseModel):
    pass


class pg_table(_PGBaseModel):
    pass


class ModelValidateRestrictedMetadataTypesNode(SingleChoiceDefinitionFlowNode):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self, name: str, restricted: list[type]):
        super().__init__(name)
        self._restricted = restricted

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for name, info in extract_definition_fields(target):
            for meta in info.metadata:
                meta_type: type = type(meta)
                if meta_type not in self._restricted:
                    errors.append(f'Invalid metadata type {meta_type} in {name} declaration')
        if len(errors) > 0:
            raise FlowNodeException(self.name, errors)


class ModelValidateUniqueMetadataTypesNode(SingleChoiceDefinitionFlowNode):
    """
    Types received must appear once in field metadata
    """

    def __init__(self, name: str, unique: list[type]):
        super().__init__(name)
        self._unique = unique

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        # extract_by_instance_type_from_model_fields_info debe obtener toda la metadata
        # hasta el type basico subyacente. por ejemplo de pg_int hasta el type
        # int subyacente
        for name, info in extract_definition_fields(target):
            classified_field_meta: dict[type, int] = get_field_classified_metadata_appearances(info)
            for unique in self._unique:
                appearances: int = classified_field_meta.get(unique, 0)
                if appearances > 1:
                    errors.append(f'Metadata type {unique} can only appear once in {name} declaration')
        if len(errors) > 0:
            raise FlowNodeException(self.name, errors)


class ModelValidateFieldsBaseTypeNode(SingleChoiceDefinitionFlowNode):
    """
    We must be sure that base type of fields will have a postgres representation
    """

    def __init__(self, name: str, *, type_subclass: list[type],
                 type_instance: list[type]) -> None:
        super().__init__(name)
        self._type_subclass = type_subclass
        self._type_instance = type_instance

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # mira el type base del campo y valida que este entre los requeridos
        errors: list[str] = []
        for name, info in extract_definition_fields(target):
            is_subclass_of_required: bool = False
            for required in self._type_subclass:
                if issubclass(extract_type(info.annotation), required):
                    is_subclass_of_required = True
            is_instance_of_required: bool = False
            if not is_subclass_of_required:
                for required in self._type_instance:
                    if isinstance(extract_type(info.annotation), required):
                        is_instance_of_required = True
            if is_subclass_of_required or is_instance_of_required:
                continue
            elif not is_instance_of_required:
                super_instances_str: str = ', '.join([str(e) for e in self._type_instance])
                errors.append(f'Field {name} type must be a subclass of {super_instances_str}')
            else:
                super_classes_str: str = ', '.join([str(e) for e in self._type_subclass])
                errors.append(f'Field {name} type must be an instance of {super_classes_str}')
        if len(errors) > 0:
            raise FlowNodeException(self.name, errors)
