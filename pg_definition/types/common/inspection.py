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
from typing import\
    Iterable


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


# TODO rename this to extract_by_instance_type_from_field_info_metadata
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


def extract_definition_fields(cls: type) -> Generator[tuple[str, FieldInfo], None, None]:
    """
    Exclude inherited fields and yield only those fields defined as table 
    attributes directly. Considerations:
    - Child class can redefine parent attribute, changes wont be detected unless
    type or metadata are modified.
    """
    direct_fields: dict[str, FieldInfo] = set(cls.model_fields.keys())
    for icls in cls.__bases__:
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


def extract_inherited_fields(cls: type) -> Generator[tuple[str, FieldInfo], None, None]:
    """
    Exclude definition fields and yield only those fields inherited from base classes
    """
    model_fields = set(cls.model_fields.keys())
    direct_fields = set([field for field, _ in extract_definition_fields(cls)])
    for inherited_field in (model_fields - direct_fields):
        yield inherited_field, cls.model_fields[inherited_field]


def extract_by_instance_type_from_model_fields_info(
    cls: type[BaseModel],
    instance_type: type,
    conversion_fn: Optional[Callable[[Any], dict[str, Any]]] = None
) -> Generator[tuple[str, dict[str, Any] | Any], None, None]:
    """
    Extracts by instance type from direct fields metadata
    """
    for field_name, field_info in extract_definition_fields(cls):
        for meta in extract_by_instance_type_from_field_info(field_info, instance_type):
            if conversion_fn is not None:
                yield field_name, conversion_fn(field_name, meta)
            else:
                yield field_name, meta


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


def get_field_parent_definition(name: str, cls: type) -> Optional[FieldInfo]:
    for icls in cls.__bases__:
        if name in icls.model_fields:
            return icls.model_fields[name]
    return None


def set_accumulator(
    set_member: Any,
    accumulator: Optional[set[Any]]
) -> set[Any]:
    if accumulator is None:
        return set[Any]((set_member, ))
    accumulator.add(set_member)
    return accumulator


def tuple_accumulator(
    member: Any,
    accumulator: Optional[set[Any]]
) -> set[Any]:
    if accumulator is None:
        return (member, )
    accumulator = (*accumulator, member)
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


def is_optional(field) -> bool:
    return get_origin(field) is Union and type(None) in get_args(field)


def extract_type(tp: type) -> type:
    if is_optional(tp):
        return get_args(tp)[0]
    return tp


def get_members(cls: type) -> dict[str, type]:
    return dict(cls.__annotations__)


def flatten(items):
    """Yield items from any nested iterable; see Reference."""
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x


def is_pg_type(name: str, tp: type, type_subclass: list[type], instances: list[type]) -> list[str]:
    errors: list[str] = []
    is_subclass_of_required: bool = False
    for required in type_subclass:
        if issubclass(tp, required):
            is_subclass_of_required = True
    is_instance_of_required: bool = False
    if not is_subclass_of_required:
        for required in instances:
            if isinstance(tp, required):
                is_instance_of_required = True
    if is_subclass_of_required or is_instance_of_required:
        return errors
    elif not is_instance_of_required:
        super_instances_str: str = ', '.join([str(e) for e in instances])
        errors.append(f'Field {name} type must be a subclass of {super_instances_str}')
    else:
        super_classes_str: str = ', '.join([str(e) for e in type_subclass])
        errors.append(f'Field {name} type must be an instance of {super_classes_str}')
    return errors
