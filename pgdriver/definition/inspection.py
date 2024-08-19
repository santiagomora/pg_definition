from typing import\
    Any,\
    Optional,\
    Callable,\
    KeysView,\
    Generator,\
    get_args,\
    get_origin,\
    Union
from pydantic.fields import\
    FieldInfo
import copy
from collections import\
    OrderedDict
from ordered_set import\
    OrderedSet
from pydantic import\
    BaseModel
from deepdiff import \
    DeepDiff


# TODO esto deberia ir en su propio archivo porque esta creciendo bastante
# la precondicion es que field_meta tenga datos, pero puede darse el caso 
# de que la meta venga vacia desde la descripcion de algun campo
# los diccionarios de field_meta deben tener todos las mismas llaves y 
# los attributos de attrs deben ser llaves validas
def key_by(
    attrs: tuple[str, ...],
    field_meta: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    if field_meta == []:
        return {}
    if len(attrs) == 0:
        return field_meta
    group: dict[str, list[Any]] = {}
    attr: str = attrs[0]
    for meta in field_meta:
        attr_value: Any = meta[attr]
        if attr_value is not None:
            if attr_value in group:
                group[attr_value].append(meta)
            else:
                group[attr_value] = [meta]
    for group_name in group:
        group[group_name] = key_by(attrs[1:], group[group_name])
    return group


def check_unaggregated_values(
    aggregation_targets: list[dict[str, Any]],
    aggregate_by_keys: dict[str, Callable[[Any, Optional[Any]], Any]]
) -> None:
    # la precondicion es que todos los targets tengan las mismas keys
    # hacer raise de los atributos que se repitan nada mas y despues 
    # lanzar el error con todos los mensajes
    if len(aggregation_targets) == 0:
        return
    target_keys: KeysView = aggregation_targets[0].keys()
    unaggregated_keys: set[str] = set()
    for key in target_keys:
        if key not in aggregate_by_keys:
            unaggregated_keys.add(key)
    if len(unaggregated_keys) == 0:
        return
    # las llaves que no participan en el agregado deben tener valores iguales
    errors: list[str] = []
    for unaggregated in unaggregated_keys:
        base_value: Any = aggregation_targets[0][unaggregated]
        try:
            for target in aggregation_targets:
                if target[unaggregated] != base_value:
                    raise ValueError(f'Unaggregated attribute has distinct values: {unaggregated!r}')
        except ValueError as e:
            errors.append(str(e))
    if len(errors) > 0:
        raise ValueError('\n'.join(errors))


# en realidad es una operacion de agregacion que necesita una funcion acumuladora
# la funcion acumuladora toma el valor actual, el acumulador y devuelve el acumulador
# def aggregate(
#     by_attributes: tuple[str, ...],
#     aggregation_targets: list[dict[str, Any]],
#     aggregation_fn: Callable[[Any, Optional[Any]], Any]
# ) -> dict[str, Any]:
#     # instance_metadata: list[tuple[str, T]] = []
#     # for field_name, field_info in fields.items():
#     #     for meta in field_info.metadata:
#     #         if isinstance(meta, instance_type):
#     #             instance_metadata.append(meta.to_description_dict(field_name))
#     if aggregation_targets == []:
#         return {}
#     check_unaggregated_values(aggregation_targets, by_attributes)
#     res: dict[str, Any] = copy.deepcopy(aggregation_targets[0])
#     for attr in by_attributes:
#         acc: Optional[Any] = None
#         for meta in aggregation_targets:
#             acc: Any = aggregation_fn(meta[attr], acc)
#             res[attr] = acc
#     return res
def aggregate(
    aggregation_targets: list[dict[str, Any]],
    by_attributes: dict[str, Callable[[Any, Optional[Any]], Any]]
) -> dict[str, Any]:
    # instance_metadata: list[tuple[str, T]] = []
    # for field_name, field_info in fields.items():
    #     for meta in field_info.metadata:
    #         if isinstance(meta, instance_type):
    #             instance_metadata.append(meta.to_description_dict(field_name))
    if aggregation_targets == []:
        return {}
    check_unaggregated_values(aggregation_targets, by_attributes)
    res: dict[str, Any] = copy.deepcopy(aggregation_targets[0])
    for attr in by_attributes:
        acc: Optional[Any] = None
        for meta in aggregation_targets:
            acc: Any = by_attributes[attr](meta[attr], acc)
            res[attr] = acc
    return res


def extract_by_instance_type_from_list(
    elem_list: list[Any],
    instance_type: type
) -> Generator[type, None, None]:
    for elem in elem_list:
        if isinstance(elem, instance_type):
            yield elem


def extract_first_appearance_from_list(
    elem_list: list[Any],
    instance_type: type
) -> Any:
    for elem in elem_list:
        if isinstance(elem, instance_type):
            return elem
    return None


def extract_by_instance_type_from_field_info(
    info: FieldInfo,
    instance_type: type
) -> Generator[type, None, None]:
    for meta in extract_by_instance_type_from_list(info.metadata, instance_type):
        yield meta


def extract_first_instance_from_field_metadata(
    info: FieldInfo,
    instance_type: type
) -> Any:
    return extract_first_appearance_from_list(info.metadata, instance_type)


def extract_definition_fields(
    cls: type,
    base_class: type[BaseModel]
) -> Generator[tuple[str, FieldInfo], None, None]:
    """
    Exclude inherited fields and yield only those fields defined as table 
    attributes directly. Considerations:
    - Child class can redefine parent attribute, changes wont be detected unless
    type or metadata are modified.
    """
    direct_fields: dict[str, FieldInfo] = set(cls.model_fields.keys())
    for icls in extract_by_instance_type_from_inherited_classes(cls, base_class):
        for inherited_field_name in icls.model_fields:
            if inherited_field_name in direct_fields:
                # if FieldInfo has not changed it means that the field is inherited
                # so we must remove it. Otherwise the field is inherited and overriden
                # in cls. It doesnt make sense to declare the field exactly as is in child
                # model
                if DeepDiff(icls.model_fields[inherited_field_name], cls.model_fields[inherited_field_name]) == {}:
                    direct_fields.remove(inherited_field_name)
    for field_name in direct_fields:
        yield (field_name, cls.model_fields[field_name])


def extract_by_instance_type_from_model_fields_info(
    cls: type[BaseModel],
    instance_type: type,
    base_class: type[BaseModel] = None,
    conversion_fn: Optional[Callable[[Any], dict[str, Any]]] = None
) -> Generator[dict[str, Any], None, None]:
    """
    Extracts by instance type from direct fields metadata
    """
    for field_name, field_info in extract_definition_fields(cls, base_class):
        for meta in extract_by_instance_type_from_field_info(field_info, instance_type):
            if conversion_fn is not None:
                yield conversion_fn(field_name, meta)
            else:
                yield meta


def get_classified_metadata_from_fields(
    base_model
) -> dict[type, str]:
    fields: dict[str, FieldInfo] = base_model.model_fields
    res: dict[type, Any] = {}
    errors: list[str] = []
    for field_name in fields:
        try:
            field: FieldInfo = fields[field_name]
            # validate_metadata(tuple(list(get_metadata_from_domain(field.annotation)) + [field.metadata]))
            for meta in field.metadata:
                metadata_type: type = type(meta)
                if metadata_type in res:
                    res[metadata_type].append(field_name)
                else:
                    res[metadata_type] = [field_name]
        except Exception as e:
            errors.append(str(e))
    if len(errors) > 0:
        raise Exception('\n'.join(errors))
    return res


def get_field_classified_metadata_appearances(
    info: FieldInfo
) -> dict[type, str]:
    res: dict[type, Any] = {}
    for meta in info.metadata:
        metadata_type: type = type(meta)
        res[metadata_type] = res.get(metadata_type, 0) + 1
    return res


# * solo nos interesan los atributos de la clase actual,
# no los de las clases heredadas
def extract_by_instance_type_from_inherited_classes(
    cls: type,
    instance_type: Optional[type] = None
) -> tuple[type]:
    instance_metadata: list[Any] = []
    # base_classes: tuple[type] = inspect.getmro(cls)
    base_classes: tuple[type] = cls.__bases__
    if instance_type is None:
        return base_classes
    for base_class in base_classes:
        if issubclass(base_class, instance_type) and base_class != cls and base_class != instance_type:
            instance_metadata.append(base_class)
    return tuple(instance_metadata)


def set_accumulator(
    set_member: Any,
    accumulator: Optional[set[Any]]
) -> set[Any]:
    if accumulator is None:
        return set[Any]((set_member, ))
    accumulator.add(set_member)
    return accumulator


def ordered_set_accumulator(
    set_member: Any,
    accumulator: Optional[OrderedSet[Any]]
) -> set[Any]:
    if accumulator is None:
        return OrderedSet[Any]((set_member, ))
    accumulator.add(set_member)
    return accumulator


# en realidad querria usar orderedset pero ordereddict va a funcionar
def ordered_dict_accumulator(
    seq_member: Any,
    accumulator: OrderedDict[Any, None]
) -> OrderedDict[Any, None]:
    if accumulator is None:
        res = OrderedDict[Any, None]()
        res[seq_member] = None
        return res
    if seq_member in accumulator:
        return accumulator
    accumulator[seq_member] = None
    accumulator.move_to_end(seq_member, last=True)
    return accumulator


def has_classattr(cls: type, methodname: str) -> bool:
    attr_name = methodname
    if methodname.startswith('__'):
        attr_name = f'_{cls.__name__}__{methodname}'
    return hasattr(cls, attr_name)


def execute_classmethod(cls: type, methodname: str, default_value: Any = None, *args, **kwargs) -> Any:
    if not has_classattr(cls, methodname):
        return default_value
    method = getattr(cls, f'_{cls.__name__}__{methodname}')
    return method(*args, **kwargs)


def delete_classattr(cls: type, methodname: str, *args, **kwargs) -> None:
    attr_name = methodname
    if methodname.startswith('__'):
        attr_name = f'_{cls.__name__}__{methodname}'
    delattr(cls, attr_name)


def get_type_arguments(cls: type) -> tuple[type]:
    arg_types: set[type] = set()
    for base in cls.__orig_bases__:
        arg_types = arg_types.union(set(get_args(base)))
    return tuple(arg_types)


def is_optional(field) -> bool:
    return get_origin(field) is Union and type(None) in get_args(field)


def extract_type(tp: type) -> type:
    if is_optional(tp):
        return get_args(tp)[0]
    return tp


def is_field_inherited(name: str, cls: type, base_class_type: type[BaseModel]) -> bool:
    for icls in extract_by_instance_type_from_inherited_classes(cls, base_class_type):
        if name in icls.model_fields:
            return True
    return False

# # * los atributos de las clases base no pueden compartirse y si
# # se comparten deben tener la misma definicion
# def check_valid_attributes_between_base_classes(
#     cls: type,
#     instance_type: type
# ) -> None:
#     base_classes = extract_by_instance_type_from_inherited_classes(cls, instance_type)
#     all_base_attrs: dict[str, FieldInfo] = {}
#     for base_class in base_classes:
#         for base_class_attr in base_class.__fields__:
#             if base_class_attr in all_base_attrs:
#                 if deepdiff.DeepDiff(all_base_attrs[base_class_attr], base_class[base_class_attr], ignore_order=True) != {}:
#                     # tengo que indicar el atributo compartido que esta fallando
#                     # y en que atributo esta fallando
#                     raise ValueError('Clases heredadas que compartan el mismo atributo deben tener la misma definicion de atributo')
#         all_base_attrs |= base_class.__fields__
# 
# 
# # liskov: puedes debilitar la precondicion y endurecer la poscondicion
# def check_valid_inherited_attributes(
#     cls: type,
#     instance_type: type
# ) -> dict[str, FieldInfo]:
#     base_classes = extract_by_instance_type_from_inherited_classes(cls, instance_type)
#     all_base_attrs: dict[str, FieldInfo] = {}
#     for base_class in base_classes:
#         all_base_attrs |= base_class.model_fields
#     for class_attr in cls.model_fields:
#         if class_attr in all_base_attrs:
#             if deepdiff.DeepDiff(all_base_attrs[class_attr], cls.model_fields[class_attr], ignore_order=True) != {}:
#                 # tengo que indicar el atributo compartido que esta fallando
#                 # y en que atributo esta fallando
#                 # en realidad me voy por el camino facil porque si yo sobreescribo
#                 # un atributo podria debilitar el check y aun asi satisfacer la condicion de la clase base por liskov
#                 raise ValueError('Atributos heredados deben tener la misma definicion que en las clases base')
