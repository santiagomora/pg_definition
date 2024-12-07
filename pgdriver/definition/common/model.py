from .flow import\
    RootDefinitionFlowNode,\
    execute_definition_flow,\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator,\
    NodeException
from pydantic import\
    BaseModel
from ..meta import\
    check,\
    OperandDefinitionContext
from .inspection import\
    get_field_classified_metadata_appearances,\
    extract_definition_fields,\
    extract_type,\
    extract_inherited_fields,\
    extract_by_instance_type_from_model_fields_info
from typing import\
    Any


composite_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('composite-definition-flow')
table_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('table-definition-flow')


class _PGBaseModelMeta(type(BaseModel)):
    def __new__(cls, clsname, clsbases, namespace, **kwargs) -> type[BaseModel]:

        rettype: type[BaseModel] = super()\
            .__new__(cls, clsname, clsbases, namespace, **(kwargs))

        try:
            if issubclass(rettype, table):
                execute_definition_flow(rettype, table_definition_flow_root)
            elif issubclass(rettype, composite):
                if len(clsbases) > 1:
                    raise TypeError(f'Class {cls} doesnt allow multiple bases')
                execute_definition_flow(rettype, composite_definition_flow_root)
        except NameError:
            pass
        return rettype


class base_model(BaseModel, metaclass=_PGBaseModelMeta):
    def __init__(self, **data: Any) -> None:
        for parent_cls in reversed(self.__class__.mro()[1:-4]):
            parent_cls.__pydantic_validator__.validate_python(data, self_instance=self)
        return super().__init__(**data)


class composite(base_model):
    pass


class table(base_model):
    pass


class ModelValidateUniqueMetadataTypesNode(SingleChoiceDefinitionFlowNode):
    """
    Types received must appear once in field metadata
    """

    def __init__(self, name: str, *, types: list[type]):
        super().__init__(name)
        self._unique = types

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        # extract_by_instance_type_from_model_fields_info debe obtener toda la metadata
        # hasta el type basico subyacente. por ejemplo de integer hasta el type
        # int subyacente
        for name, info in extract_definition_fields(target):
            classified_field_meta: dict[type, int] = get_field_classified_metadata_appearances(info)
            for unique in self._unique:
                appearances: int = classified_field_meta.get(unique, 0)
                if appearances > 1:
                    errors.append(f'Metadata type {unique} can only appear once in {name} declaration')
        if len(errors) > 0:
            raise NodeException(self.name, errors)


class ModelDiscardMetaInstancesFromInheritedFieldsNode(SingleChoiceDefinitionFlowNode):
    """
    All inherited metadata gets discarded. Initially it was planned to keep checks and default values, but as parent validation gets applied when creating an instance, this is not necessary.
    Postgres itself will be in charge to add all parent check constraints by itself when declaring the inheritance over the child class.
    """

    def __init__(self, name: str):
        super().__init__(name)

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        for field, info in extract_inherited_fields(target):
            target.model_fields[field].metadata = []
        target.model_rebuild(force=True)


class ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode(SingleChoiceDefinitionFlowNode):
    def __init__(self, name: str, *, types: tuple[type, ...]):
        super().__init__(name)
        self._types = types

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        name_count: dict[str, int] = {}
        errors: list[str] = []
        for tp in self._types:
            for field_name, instance in extract_by_instance_type_from_model_fields_info(target, tp):
                abs_name: str = f'{field_name}.{instance.name}.{tp.__name__}'
                name_count[abs_name] = name_count.get(abs_name, 0) + 1
        for name in name_count:
            if name_count[name] > 1:
                field_name, instance_name, tp_name = name.split('.')
                # this means there is two instances of same type that share name
                errors.append(f'Metadata definition error in {field_name}: found {name_count[name]} repeated instances of same type {tp_name} sharing name {instance_name}.')
        if len(errors) > 0:
            raise NodeException(self.name, errors)


class ModelExtractCheckConstraintsNode(SingleChoiceDefinitionFlowNode):
    def __init__(self, name: str, context: OperandDefinitionContext):
        super().__init__(name)
        self._context = context

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        checks: dict[str, check] = {}
        for field, ck in extract_by_instance_type_from_model_fields_info(target, check):
            ck.predicate.propagate_definition(target.model_fields[field].annotation, field, self._context)
            ck.name = f'{target.__name__}_{ck.name}'
            if ck.name not in checks:
                checks[ck.name] = ck
            else:
                checks[ck.name].predicate = checks[ck.name].predicate & ck.predicate
        accumulator.add_definition('check_constraints', checks if checks != {} else None)
