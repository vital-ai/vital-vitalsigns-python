from vital_ai_vitalsigns.metaql.constraint.metaql_constraint import COMPARATOR_TYPE_EXISTS, COMPARATOR_TYPE_NOT_EXISTS, \
    COMPARATOR_TYPE_EQUAL_TO, COMPARATOR_TYPE_NOT_EQUAL_TO, COMPARATOR_TYPE_LESS_THAN, COMPARATOR_TYPE_GREATER_THAN, \
    COMPARATOR_TYPE_LESS_THAN_EQUAL_TO, COMPARATOR_TYPE_GREATER_THAN_EQUAL_TO, COMPARATOR_TYPE_ONE_OF_LIST, \
    COMPARATOR_TYPE_NONE_OF_LIST, COMPARATOR_TYPE_LIST_CONTAINS, COMPARATOR_TYPE_LIST_NOT_CONTAINS, \
    COMPARATOR_TYPE_STRING_CONTAINS, COMPARATOR_TYPE_STRING_NOT_CONTAINS


class ComparatorTypeUtils:

    @staticmethod
    def lookup_comparator_type(comparator):

        from vital_ai_vitalsigns.metaql.query.query_builder import ConstraintType

        metaql_comparator = None

        if comparator == ConstraintType.EXISTS:
            metaql_comparator = COMPARATOR_TYPE_EXISTS

        if comparator == ConstraintType.NOT_EXISTS:
            metaql_comparator = COMPARATOR_TYPE_NOT_EXISTS

        if comparator == ConstraintType.EQUAL_TO:
            metaql_comparator = COMPARATOR_TYPE_EQUAL_TO

        if comparator == ConstraintType.NOT_EQUAL_TO:
            metaql_comparator = COMPARATOR_TYPE_NOT_EQUAL_TO

        if comparator == ConstraintType.LESS_THAN:
            metaql_comparator = COMPARATOR_TYPE_LESS_THAN

        if comparator == ConstraintType.GREATER_THAN:
            metaql_comparator = COMPARATOR_TYPE_GREATER_THAN

        if comparator == ConstraintType.LESS_THAN_OR_EQUAL:
            metaql_comparator = COMPARATOR_TYPE_LESS_THAN_EQUAL_TO

        if comparator == ConstraintType.GREATER_THAN_OR_EQUAL:
            metaql_comparator = COMPARATOR_TYPE_GREATER_THAN_EQUAL_TO

        if comparator == ConstraintType.ONE_OF:
            metaql_comparator = COMPARATOR_TYPE_ONE_OF_LIST

        if comparator == ConstraintType.NONE_OF:
            metaql_comparator = COMPARATOR_TYPE_NONE_OF_LIST

        if comparator == ConstraintType.LIST_CONTAINS:
            metaql_comparator = COMPARATOR_TYPE_LIST_CONTAINS

        if comparator == ConstraintType.LIST_NOT_CONTAINS:
            metaql_comparator = COMPARATOR_TYPE_LIST_NOT_CONTAINS

        if comparator == ConstraintType.STRING_CONTAINS:
            metaql_comparator = COMPARATOR_TYPE_STRING_CONTAINS

        if comparator == ConstraintType.STRING_NOT_CONTAINS:
            metaql_comparator = COMPARATOR_TYPE_STRING_NOT_CONTAINS

        return metaql_comparator
