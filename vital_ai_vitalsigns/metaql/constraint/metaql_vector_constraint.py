from typing import Literal, List

from vital_ai_vitalsigns.metaql.constraint.metaql_constraint import MetaQLConstraint

VECTOR_CONSTRAINT_TYPE_TEXT = "VECTOR_CONSTRAINT_TYPE_TEXT"
VECTOR_CONSTRAINT_TYPE_VECTOR = "VECTOR_CONSTRAINT_TYPE_VECTOR"


VECTOR_CONSTRAINT_TYPE = Literal[
    "VECTOR_CONSTRAINT_TYPE_TEXT",
    "VECTOR_CONSTRAINT_TYPE_VECTOR"
]

VECTOR_COMPARATOR_TYPE_NEAR_TO = "VECTOR_COMPARATOR_TYPE_NEAR_TO"
VECTOR_COMPARATOR_TYPE_FAR_FROM = "VECTOR_COMPARATOR_TYPE_FAR_FROM"

VECTOR_COMPARATOR_TYPE = Literal[
    "VECTOR_COMPARATOR_TYPE_NEAR_TO",
    "VECTOR_COMPARATOR_TYPE_FAR_FROM"
]


class VectorConstraint(MetaQLConstraint):

    vector_constraint_type: VECTOR_CONSTRAINT_TYPE
    vector_comparator_type: VECTOR_COMPARATOR_TYPE
    class_uri: str
    vector_name: str


class VectorConstraintTextValue(VectorConstraint):
    text_constraint_value: str


class VectorConstraintVectorValue(VectorConstraint):
    vector_constraint_value: List[float]

