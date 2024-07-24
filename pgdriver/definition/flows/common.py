from pgdriver.definition.base import\
    FlowComponent,\
    FlowAccumulator,\
    FlowComponentException
from pgdriver.definition.types.builtin import\
    pg_builtin
from pgdriver.definition.tools.inspection import\
    get_field_classified_metadata_appearances
from pgdriver.definition.flows import\
    T
from pgdriver.definition.tools.metadata import\
    pg_comment_meta,\
    pg_check_meta


class CommonValidateRestrictedMetadataTypesComponent(FlowComponent[T]):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self, restricted: list[type]):
        super().__init__('validate-restricted-metadata-types-component')
        self._restricted = restricted

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for name, info in target.model_fields.items():
            for meta in info.metadata:
                meta_type: type = type(meta)
                if meta_type not in self._restricted:
                    errors.append(f'Invalid metadata type {meta_type} in {name} declaration')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


class CommonValidateUniqueMetadataTypesComponent(FlowComponent[T]):
    """
    Types received must appear once in field metadata
    """

    def __init__(self, unique: list[type]):
        super().__init__('validate-unique-metadata-type-component')
        self._unique = unique

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        # extract_by_instance_type_from_model_fields_info debe obtener toda la metadata
        # hasta el type basico subyacente. por ejemplo de pg_int hasta el type
        # int subyacente
        for name, info in target.model_fields.items():
            classified_field_meta: dict[type, int] = get_field_classified_metadata_appearances(info)
            for unique in self._unique:
                appearances: int = classified_field_meta.get(unique, 0)
                if appearances > 1:
                    errors.append(f'Metadata type {unique.__name__} can only appear once in {name} declaration')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


class CommonValidateBaseTypesComponent(FlowComponent[T]):
    """
    We must be sure that base type of fields will have a postgres representation
    """

    def __init__(self, required: list[type]):
        super().__init__('validate-required-metadata-types-component')
        self._required = required

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        # mira el type base del campo y valida que este entre los requeridos
        errors: list[str] = []
        super_types: str = ', '.join([e.__name__ for e in self._required])
        for name, info in target.model_fields.items():
            is_subclass_of_required: bool = False
            for required in self._required:
                if issubclass(info.annotation, required) or isinstance(info.annotation, pg_builtin):
                    is_subclass_of_required = True
            if not is_subclass_of_required:
                errors.append(f'Field {name} must be a subtype of {super_types}')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


class CommonExtractCheckDefinitionComponent(FlowComponent[T]):
    """
    Extract check constraints
    """

    def __init__(self):
        super().__init__('extract-check-definition-component')

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        attr_name: str = f'_{target.__name__}__pg_check_meta'
        if hasattr(target, attr_name):
            check: pg_check_meta = getattr(target, attr_name)()
            accumulator.add_definition('check', check.predicate.as_str(target.__name__))


class CommonExtractCommentDefinitionComponent(FlowComponent[T]):
    """
    Extract comments
    """

    def __init__(self):
        super().__init__('extract-comment-definition-component')

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        attr_name: str = f'_{target.__name__}__pg_comment_meta'
        if hasattr(target, attr_name):
            comment: pg_comment_meta = getattr(target, attr_name)()
            accumulator.add_definition('comment', comment.value)


# los types pueden heredar unicamente del type base
class CommonValidateSingleInheritedClassComponent:
    def __init__(self):
        super().__init__('extract-comment-definition-component')

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        attr_name: str = f'_{target.__name__}__pg_comment_meta'
        if hasattr(target, attr_name):
            comment: pg_comment_meta = getattr(target, attr_name)()
            accumulator.add_definition('comment', comment.value)
    pass
