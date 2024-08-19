from .flow import\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator,\
    FlowNodeException,\
    MultipleChoiceDefinitionFlowNode
from ...inspection import\
    get_field_classified_metadata_appearances,\
    extract_by_instance_type_from_inherited_classes,\
    extract_by_instance_type_from_model_fields_info,\
    has_classattr,\
    extract_first_instance_from_field_metadata,\
    extract_by_instance_type_from_list,\
    extract_first_appearance_from_list,\
    extract_definition_fields,\
    execute_classmethod,\
    delete_classattr,\
    extract_type
from .meta import\
    pg_model_field_check
from typing import\
    Optional,\
    Any


class CommonValidateRestrictedMetadataTypesNode(SingleChoiceDefinitionFlowNode):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self,
                 name: str,
                 restricted: list[type]):
        super().__init__(name)
        self._restricted = restricted

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for name, info in target.model_fields.items():
            for meta in info.metadata:
                meta_type: type = type(meta)
                if meta_type not in self._restricted:
                    errors.append(f'Invalid metadata type {meta_type} in {name} declaration')
        if len(errors) > 0:
            raise FlowNodeException(self.name, errors)


class CommonValidateUniqueMetadataTypesNode(SingleChoiceDefinitionFlowNode):
    """
    Types received must appear once in field metadata
    """

    def __init__(self,
                 name: str,
                 unique: list[type]):
        super().__init__(name)
        self._unique = unique

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        # extract_by_instance_type_from_model_fields_info debe obtener toda la metadata
        # hasta el type basico subyacente. por ejemplo de pg_int hasta el type
        # int subyacente
        for name, info in target.model_fields.items():
            classified_field_meta: dict[type, int] = get_field_classified_metadata_appearances(info)
            for unique in self._unique:
                appearances: int = classified_field_meta.get(unique, 0)
                if appearances > 1:
                    errors.append(f'Metadata type {unique} can only appear once in {name} declaration')
        if len(errors) > 0:
            raise FlowNodeException(self.name, errors)


class CommonValidateSingleInheritedClassNode(SingleChoiceDefinitionFlowNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.is_domain = Optional[bool]

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        base_classes: tuple[type] = extract_by_instance_type_from_inherited_classes(target)
        if len(base_classes) > 1:
            raise FlowNodeException(self.name, f'Type {target} can only have one base class: {self._base_class}')


class CommonDetermineIfTargetIsDomainNode(MultipleChoiceDefinitionFlowNode):
    """
    Types can only inherit from base_class, if they inherit from a subclass of the 
    base class, then they will be considered as domain. A definition in the accumulator
    will be added accordingly
    """

    def __init__(self, name: str, base_class: type):
        super().__init__(2, name)
        self._base_class = base_class
        self.is_domain: Optional[bool] = None

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        base_class: tuple[type] = extract_by_instance_type_from_inherited_classes()[0]
        self.is_domain = base_class is not self._base_class


class CommonValidateFieldsBaseTypeNode(SingleChoiceDefinitionFlowNode):
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
        for name, info in target.model_fields.items():
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


class CommonExtractCheckConstraintsNode(SingleChoiceDefinitionFlowNode):
    """
    Extracts check constraint from fields
    """

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        constraints: list[pg_model_field_check] = \
            [const for const in
             extract_by_instance_type_from_model_fields_info(target,
                                                             pg_model_field_check,
                                                             self._base_class,
                                                             lambda field_name, ck: {'ck_check_meta': ck,
                                                                                     'ck_field_name': field_name})]
        if len(constraints) > 0:
            accumulator.add_definition('check_constraints', constraints)


class CommonStoreCheckConstraintsNode(SingleChoiceDefinitionFlowNode):
    """
    Stores check constraint extracted from fields
    """

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('check_constraints',
                                                                      'extraction')
        if definition is None:
            return
        cks: list[pg_model_field_check] = [pg_model_field_check(**ck) for ck in definition]

        @classmethod
        def __pg_model_field_check_constraints(cls) -> list[pg_model_field_check]:
            return cks

        accumulator.add_definition('__pg_model_field_check_constraints', __pg_model_field_check_constraints)


class ValidatesConflictingDefinitions:
    """
    Used to validate that inferred definitions fon interfere with 
    those injected through decorators
    """

    def check_conflicting_definitions(self, target: type,
                                      definition_name: str) -> None:
        if has_classattr(target, f'__pg_{definition_name}'):
            raise FlowNodeException(target.name, [f'Conflicting definition {definition_name} for component {self._name}'])


class CommonMergeInheritedFieldsNode(SingleChoiceDefinitionFlowNode):
    """
    Pydantic overrides parent fields when redefined on child tables, losing
    parent field metadata, and allowing child models that would be invalid
    parent models.

    'A serious limitation of the inheritance feature is that indexes (including unique constraints) 
    and foreign key constraints only apply to single tables, not to their inheritance children. 
    This is true on both the referencing and referenced sides of a foreign key constraint. '

    Inherited fields must follow postgres rules when inheriting from table:
    - Data type: field type defined in child table must match parent field type
    - Default value: child table must inherit default value from parent, cant 
    define a different one
    - Foreign key: can be redefined, as they will be interpreted as a
    child table primary key
    - Primary key: can be redefined, as they will be interpreted as a
    child table primary key
    - Check constraints: will be merged by conjunction, as a child table 
    instance must be a valid parent table instance. Programmer must avoid mutually 
    exclusive constraints, as they wont be detected
    - Unique index: can be redefined, as they will be interpreted as a
    child table primary key
    """

    def __init__(self, name: str, target_type: type, inheritable_meta_types: tuple[type],
                 mergeable_meta_types: tuple[type]) -> None:
        super().__init__(name)
        self._target_type = target_type
        self._inheritable_meta_types = inheritable_meta_types
        self._mergeable_meta_types = mergeable_meta_types

    def _merge_from_parents(self, target: type, overwritten_fields: dict[str, list[Any]],
                            meta_type: type) -> None:
        # meta_type must be mergeable
        for name in overwritten_fields:
            # Extract mergeable from parent meta and merge with that defined in child
            # There is at most one mergeable instance in field metadata, per previous 
            # validations
            mergeable_child_instance: Optional[Any] = extract_first_instance_from_field_metadata(target.model_fields[name],
                                                                                                 meta_type)
            mergeable_inherited_instances: list[Any] = [c for c in extract_by_instance_type_from_list(overwritten_fields[name],
                                                                                                      meta_type)]
            if len(mergeable_inherited_instances) <= 0:
                return
            if mergeable_child_instance is None:
                # merges parent instances and then field in child inherits
                # the merged instance
                target.model_fields[name].metadata.append(mergeable_inherited_instances[0].merge(mergeable_inherited_instances[1:]))
            else:
                mergeable_child_instance.merge(mergeable_inherited_instances)

    def _inherit_from_parents(self, target: type, overwritten_fields: dict[str, list[Any]],
                              meta_type: type) -> None:
        # the precondition is that inherited metadata instances are all consistent
        # accross parent classes, otherwise postgres raises an error. this applies 
        # both on default values and sequences
        for name in overwritten_fields:
            # validate default values or set if not defined in current model
            child_defined: Optional[Any] = extract_first_instance_from_field_metadata(target.model_fields[name],
                                                                                      meta_type)
            parent_defined: Optional[Any] = extract_first_appearance_from_list(overwritten_fields[name],
                                                                               meta_type)
            if child_defined is None and parent_defined is not None:
                # inherit parent default value
                target.model_fields[name].annotation.append(parent_defined)

    def _validate_consistent_inherited_metadata(self, target: type,
                                                overwritten_fields: dict[str, list[Any]],
                                                meta_type: type) -> list[str]:
        # Extract default values and validate all equal
        errors: list[str] = []
        for name in overwritten_fields:
            initial: Optional[Any] = extract_first_instance_from_field_metadata(target.model_fields[name],
                                                                                meta_type)
            inherited_meta: list[Any] = extract_by_instance_type_from_list(overwritten_fields[name],
                                                                           meta_type)
            if not meta_type.consistent_list([initial] + inherited_meta if initial is not None else inherited_meta):
                errors.append(f'Inconsistencies detected in inherited field {name} metadata {meta_type}')
        return errors

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        overwritten_fields: dict[str, list[Any]] = dict()
        # We are going to loop over base class fields and extract the instances
        # that need to be merged, considering that at this point the target
        # is well defined
        for name, info in extract_definition_fields(target, self._target_type):
            for icls in extract_by_instance_type_from_inherited_classes(target,
                                                                        self._target_type):
                if name in icls.model_fields:
                    # Validate fields share the same type
                    if icls.model_fields[name].annotation != info.annotation:
                        errors.append(f'Overwritten field {name} type in {target} must match with type defined in parent class {icls}')
                    info: list[Any] = overwritten_fields.get(name, [])
                    info += icls.model_fields[name].metadata
        # At this point all metadata from inherited fields is in the overwritten_fields 
        # dictionary, we must extract by instance and validate accordingly, or merge the
        # fields there are two possible cases:
        # 1. overridden field doesnt change default value/nextval, then the default 
        # value must pass to child field
        # 2. overridden field changes default value/nextval, this is illegal
        for inheritable_meta in self._inheritable_meta_types:
            errors += self._validate_consistent_inherited_metadata(target,
                                                                   overwritten_fields,
                                                                   inheritable_meta)
        if len(errors) > 0:
            raise FlowNodeException(self.name, errors)
        for mergeable_meta in self._mergeable_meta_types:
            self._merge_from_parents(target, overwritten_fields, mergeable_meta)
        for inheritable_meta in self._inheritable_meta_types:
            self._inherit_from_parents(target, overwritten_fields, inheritable_meta)
        target.model_rebuild(force=True)


# class TableMergeInheritedFieldsNode(SingleChoiceDefinitionFlowNode):
#     """
#     Pydantic overrides parent fields when redefined on child tables, losing
#     parent field metadata, and allowing child models that would be invalid
#     parent models.
# 
#     'A serious limitation of the inheritance feature is that indexes (including unique constraints) 
#     and foreign key constraints only apply to single tables, not to their inheritance children. 
#     This is true on both the referencing and referenced sides of a foreign key constraint. '
# 
#     Inherited fields must follow postgres rules when inheriting from table:
#     - Data type: field type defined in child table must match parent field type
#     - Default value: child table must inherit default value from parent, cant 
#     define a different one
#     - Foreign key: can be redefined, as they will be interpreted as a
#     child table primary key
#     - Primary key: can be redefined, as they will be interpreted as a
#     child table primary key
#     - Check constraints: will be merged by conjunction, as a child table 
#     instance must be a valid parent table instance. Programmer must avoid mutually 
#     exclusive constraints, as they wont be detected
#     - Unique index: can be redefined, as they will be interpreted as a
#     child table primary key
#     """
# 
#     def __init__(self):
#         super().__init__('merge-inherited-fields-node')
# 
#     def _merge_from_parents(self, target: type, overwritten_fields: dict[str, list[Any]], meta_type: type) -> None:
#         # meta_type must be mergeable
#         for name in overwritten_fields:
#             # Extract mergeable from parent meta and merge with that defined in child
#             # There is at most one mergeable instance in field metadata, per previous 
#             # validations
#             mergeable_child_instance: Optional[Any] = extract_first_instance_from_field_metadata(target.model_fields[name], meta_type)
#             mergeable_inherited_instances: list[Any] = [c for c in extract_by_instance_type_from_list(overwritten_fields[name], meta_type)]
#             if len(mergeable_inherited_instances) <= 0:
#                 return
#             if mergeable_child_instance is None:
#                 # merges parent instances and then field in child inherits
#                 # the merged instance
#                 target.model_fields[name].metadata.append(mergeable_inherited_instances[0].merge(mergeable_inherited_instances[1:]))
#             else:
#                 mergeable_child_instance.merge(mergeable_inherited_instances)
# 
#     def _inherit_from_parents(self, target: type, overwritten_fields: dict[str, list[Any]], meta_type: type) -> None:
#         # the precondition is that inherited metadata instances are all consistent
#         # accross parent classes, otherwise postgres raises an error. this applies 
#         # both on default values and sequences
#         for name in overwritten_fields:
#             # validate default values or set if not defined in current model
#             child_defined: Optional[Any] = extract_first_instance_from_field_metadata(target.model_fields[name], meta_type)
#             parent_defined: Optional[Any] = extract_first_appearance_from_list(overwritten_fields[name], meta_type)
#             if child_defined is None and parent_defined is not None:
#                 # inherit parent default value
#                 target.model_fields[name].annotation.append(parent_defined)
# 
#     def _validate_consistent_inherited_metadata(self, target: type, overwritten_fields: dict[str, list[Any]], meta_type: type) -> list[str]:
#         # Extract default values and validate all equal
#         errors: list[str] = []
#         for name in overwritten_fields:
#             initial: Optional[Any] = extract_first_instance_from_field_metadata(target.model_fields[name], meta_type)
#             inherited_meta: list[Any] = extract_by_instance_type_from_list(overwritten_fields[name], meta_type)
#             if not meta_type.consistent_list([initial] + inherited_meta if initial is not None else inherited_meta):
#                 errors.append(f'Inconsistencies detected in inherited field {name} metadata {meta_type}')
#         return errors
# 
#     def execute(self, target: type, accumulator: FlowAccumulator) -> None:
#         errors: list[str] = []
#         overwritten_fields: dict[str, list[Any]] = dict()
#         # We are going to loop over base class fields and extract the instances
#         # that need to be merged, considering that at this point the target
#         # is well defined
#         for name, info in extract_definition_fields(target, pg_table):
#             for icls in extract_by_instance_type_from_inherited_classes(target, pg_table):
#                 if name in icls.model_fields:
#                     # Validate fields share the same type
#                     if icls.model_fields[name].annotation != info.annotation:
#                         errors.append(f'Overwritten field {name} type in {target} must match with type defined in parent class {icls}')
#                     info: list[Any] = overwritten_fields.get(name, [])
#                     info += icls.model_fields[name].metadata
#         # At this point all metadata from inherited fields is in the overwritten_fields 
#         # dictionary, we must extract by instance and validate accordingly, or merge the
#         # fields there are two possible cases:
#         # 1. overridden field doesnt change default value/nextval, then the default 
#         # value must pass to child field
#         # 2. overridden field changes default value/nextval, this is illegal
#         errors += self._validate_consistent_inherited_metadata(target, overwritten_fields, pg_table_meta.default.value)
#         errors += self._validate_consistent_inherited_metadata(target, overwritten_fields, pg_table_meta.default.nextval)
#         if len(errors) > 0:
#             raise FlowNodeException(self.name, errors)
#         self._merge_from_parents(target, overwritten_fields, pg_table_meta.check)
#         self._inherit_from_parents(target, overwritten_fields, pg_table_meta.default.value)
#         self._inherit_from_parents(target, overwritten_fields, pg_table_meta.default.nextval)
#         target.model_rebuild(force=True)
# 
#     def get_dependencies(self) -> tuple[str]:
#         return ('validate-consistent-base-classes-node',
#                 'validate-restricted-metadata-types-node',
#                 'validate-unique-metadata-types-node',
#                 'validate-fields-base-type-node',
#                 'validate-existing-columns-node')
