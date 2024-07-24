from pgdriver.definition.flows.table import\
    TableValidateRestrictedMetadataTypesComponent,\
    TableValidateUniqueMetadataTypesComponent,\
    TableValidateInheritedFieldsComponent,\
    TableValidateBaseTypesComponent,\
    TableValidateInheritedFieldsComponent,\
    TableValidateConsistentForeignKeysComponent,\
    TableValidateConsistentBaseClassesComponent,\
    TableExtractIndexDefinitionFromDeclarationComponent,\
    TableExtractPrimaryKeyDefinitionFromDeclarationComponent,\
    TableExtractForeignKeyDefinitionFromDeclarationComponent,\
    TableExtractUniqueIndexDefinitionFromDeclarationComponent,\
    TableExtractInheritanceDefinitionFromDeclarationComponent,\
    TableExtractColumnDefinitionFromDeclarationComponent,\
    TableValidateExtractedForeignKeyDefinitionComponent,\
    TableValidateExtractedUniqueIndexDefinitionComponent,\
    TableValidateExtractedPrimaryKeyDefinitionComponent,\
    TableValidateTypeInheritanceComponent
from pgdriver.definition.flows.common import\
    CommonValidateRestrictedMetadataTypesComponent,\
    CommonValidateUniqueMetadataTypesComponent,\
    CommonValidateBaseTypesComponent,\
    CommonExtractCheckDefinitionComponent,\
    CommonExtractCommentDefinitionComponent,\
    CommonValidateSingleInheritedClassComponent
from pgdriver.definition.flows.composite import\
    CompositeExtractAttributesDefinitionComponent,\
    CompositeExtractCheckDefinitionComponent
from pgdriver.definition.flows.domain import\
    DomainValidateTargetMetaclassComponent
from pgdriver.definition.flows.enum import\
    EnumValidateTargetMetaclassComponent,\
    EnumExtractValuesComponent
from pgdriver.definition.flows import\
    DefinitionFlow,\
    DefinitionFlowRegistry
from pgdriver.definition.tools import\
    pg_domain,\
    pg_composite,\
    pg_enum,\
    pg_table
from pgdriver.definition.tools.metadata import\
    pg_foreign_key_meta,\
    pg_primary_key_meta,\
    pg_index_meta,\
    pg_unique_index_meta,\
    pg_check_meta,\
    pg_comment_meta
from pgdriver.definition.tools import\
    pg_builtin


pgdriver_definition_flow_registry = DefinitionFlowRegistry('pgdriver-definition-flow-registry')


# COMPOSITE
pgcomposite_definition_flow: DefinitionFlow[pg_composite] = DefinitionFlow[pg_composite]('pgdriver-composite-definition-flow', pg_composite)
# Validation
pgcomposite_definition_flow.register_component(
    CommonValidateSingleInheritedClassComponent())
pgcomposite_definition_flow.register_component(
    CommonValidateRestrictedMetadataTypesComponent([
        pg_check_meta]))
pgcomposite_definition_flow.register_component(
    CommonValidateUniqueMetadataTypesComponent([
        pg_check_meta]))
pgcomposite_definition_flow.register_component(
    CommonValidateBaseTypesComponent([
        pg_enum,
        pg_composite,
        pg_builtin,
        pg_domain]))
# Extraction
pgcomposite_definition_flow.register_component(
    CommonExtractCommentDefinitionComponent())
pgcomposite_definition_flow.set_critical_component('extract-comment-definition-component')
pgcomposite_definition_flow.register_component(
    CommonExtractCheckDefinitionComponent())
pgcomposite_definition_flow.register_component(
    CompositeExtractAttributesDefinitionComponent())
pgcomposite_definition_flow.register_component(
    CompositeExtractCheckDefinitionComponent())
# REGISTER FLOW
pgdriver_definition_flow_registry.register_definition_flow(pgcomposite_definition_flow)


# DOMAIN
pgdomain_definition_flow: DefinitionFlow[pg_domain] = DefinitionFlow[pg_domain]('pgdriver-domain-definition-flow', pg_domain)
pgdomain_definition_flow.register_component(
    DomainValidateTargetMetaclassComponent())
pgdomain_definition_flow.register_component(
    CommonExtractCommentDefinitionComponent())
pgdomain_definition_flow.set_critical_component('extract-comment-definition-component')
pgdomain_definition_flow.register_component(
    CommonExtractCheckDefinitionComponent())
# REGISTER FLOW
pgdriver_definition_flow_registry.register_definition_flow(pgdomain_definition_flow)


# TABLE
pgtable_definition_flow: DefinitionFlow[pg_table] = DefinitionFlow[pg_table]('pgdriver-table-definition-flow', pg_table)
# Validation
pgtable_definition_flow.register_component(
    TableValidateConsistentBaseClassesComponent())
pgtable_definition_flow.register_component(
    TableValidateInheritedFieldsComponent())
pgtable_definition_flow.register_component(
    CommonValidateRestrictedMetadataTypesComponent([
        pg_foreign_key_meta,
        pg_primary_key_meta,
        pg_index_meta,
        pg_unique_index_meta,
        pg_check_meta,
        pg_comment_meta]))
pgtable_definition_flow.register_component(
    CommonValidateUniqueMetadataTypesComponent([
        pg_foreign_key_meta,
        pg_primary_key_meta,
        pg_unique_index_meta,
        pg_comment_meta,
        pg_check_meta]))
pgtable_definition_flow.register_component(
    CommonValidateBaseTypesComponent([
        pg_enum,
        pg_builtin,
        pg_composite,
        pg_domain]))
# Extraction
pgtable_definition_flow.register_component(
    TableExtractIndexDefinitionFromDeclarationComponent())
pgtable_definition_flow.set_critical_component('extract-index-definition-from-declaration-component')
pgtable_definition_flow.register_component(
    TableExtractPrimaryKeyDefinitionFromDeclarationComponent())
pgtable_definition_flow.register_component(
    TableExtractForeignKeyDefinitionFromDeclarationComponent())
pgtable_definition_flow.register_component(
    TableExtractUniqueIndexDefinitionFromDeclarationComponent())
pgtable_definition_flow.register_component(
    TableExtractInheritanceDefinitionFromDeclarationComponent())
pgtable_definition_flow.register_component(
    TableExtractColumnDefinitionFromDeclarationComponent())
# Validate Extracted Definition
pgtable_definition_flow.register_component(
    TableValidateExtractedForeignKeyDefinitionComponent())
pgtable_definition_flow.set_critical_component('validate-extracted-foreign-key-definition-component')
pgtable_definition_flow.register_component(
    TableValidateExtractedUniqueIndexDefinitionComponent())
pgtable_definition_flow.register_component(
    TableValidateExtractedPrimaryKeyDefinitionComponent())
# REGISTER FLOW
pgdriver_definition_flow_registry.register_definition_flow(pgtable_definition_flow)


# ENUMS
pgenum_definition_flow: DefinitionFlow[pg_enum] = DefinitionFlow[pg_enum]('pgdriver-enum-definition-flow', pg_enum)
pgenum_definition_flow.register_component(
    EnumValidateTargetMetaclassComponent())
pgenum_definition_flow.register_component(
    EnumExtractValuesComponent())
pgenum_definition_flow.register_component(
    CommonExtractCommentDefinitionComponent())
pgenum_definition_flow.set_critical_component('extract-comment-definition-component')
# REGISTER FLOW
pgdriver_definition_flow_registry.register_definition_flow(pgenum_definition_flow)


__all__ = {
    'pgdriver_definition_flow_registry': pgdriver_definition_flow_registry}
