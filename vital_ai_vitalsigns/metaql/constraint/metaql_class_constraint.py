from typing import Literal
from vital_ai_vitalsigns.metaql.constraint.metaql_constraint import MetaQLConstraint


NODE_CLASS_CONSTRAINT_TYPE = "NODE_CLASS_CONSTRAINT_TYPE"
EDGE_CLASS_CONSTRAINT_TYPE = "EDGE_CLASS_CONSTRAINT_TYPE"
HYPER_NODE_CLASS_CONSTRAINT_TYPE = "HYPER_NODE_CLASS_CONSTRAINT_TYPE"
HYPER_EDGE_CLASS_CONSTRAINT_TYPE = "HYPER_EDGE_CLASS_CONSTRAINT_TYPE"


CLASS_CONSTRAINT_TYPE = Literal[
    "NODE_CLASS_CONSTRAINT_TYPE",
    "EDGE_CLASS_CONSTRAINT_TYPE",
    "HYPER_NODE_CLASS_CONSTRAINT_TYPE",
    "HYPER_EDGE_CLASS_CONSTRAINT_TYPE"
]


class ClassConstraint(MetaQLConstraint):

    class_constraint_type: CLASS_CONSTRAINT_TYPE
    class_uri: str
    include_subclasses: bool


class NodeConstraint(ClassConstraint):
    pass


class EdgeConstraint(ClassConstraint):
    pass


class HyperNodeConstraint(ClassConstraint):
    pass


class HyperEdgeConstraint(ClassConstraint):
    pass

