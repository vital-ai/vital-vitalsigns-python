from enum import Enum
from typing import List

from vital_ai_vitalsigns.metaql.arc.metaql_arc import ARC_TRAVERSE_TYPE, ARC_DIRECTION_TYPE
from vital_ai_vitalsigns.metaql.arc_list.metaql_arc_list import AND_ARC_LIST_TYPE, OR_ARC_LIST_TYPE
from vital_ai_vitalsigns.metaql.constraint.metaql_class_constraint import NODE_CLASS_CONSTRAINT_TYPE, \
    EDGE_CLASS_CONSTRAINT_TYPE

from vital_ai_vitalsigns.metaql.constraint.metaql_property_constraint import TARGET_TYPE_NODE, \
    TARGET_TYPE_EDGE

from vital_ai_vitalsigns.metaql.constraint_list.metaql_constraint_list import AND_CONSTRAINT_LIST_TYPE, \
    OR_CONSTRAINT_LIST_TYPE

from vital_ai_vitalsigns.metaql.metaql_builder import MetaQLBuilder

from vital_ai_vitalsigns.metaql.metaql_query import SelectQuery as MetaQLSelectQuery, METAQL_SELECT_QUERY, \
    METAQL_GRAPH_QUERY, METAQL_AGGREGATE_SELECT_QUERY, METAQL_AGGREGATE_GRAPH_QUERY

from vital_ai_vitalsigns.metaql.query.comparator_type_utils import ComparatorTypeUtils
from vital_ai_vitalsigns.metaql.query.property_data_constraint_utils import PropertyDataConstraintUtils
from vital_ai_vitalsigns.metaql.query.property_utils import PropertyUtils
from vital_ai_vitalsigns.vitalsigns import VitalSigns


class ConstraintType(Enum):
    EQUAL_TO = "ConstraintType_EQUAL_TO"
    NOT_EQUAL_TO = "ConstraintType_NOT_EQUAL_TO"
    LESS_THAN = "ConstraintType_LESS_THAN"
    GREATER_THAN = "ConstraintType_GREATER_THAN"
    LESS_THAN_OR_EQUAL = "ConstraintType_LESS_THAN_OR_EQUAL"
    GREATER_THAN_OR_EQUAL = "ConstraintType_GREATER_THAN_OR_EQUAL"
    EXISTS = "ConstraintType_EXISTS"
    NOT_EXISTS = "ConstraintType_NOT_EXISTS"
    ONE_OF = "ConstraintType_ONE_OF"
    NONE_OF = "ConstraintType_NONE_OF"
    LIST_CONTAINS = "ConstraintType_LIST_CONTAINS"
    LIST_NOT_CONTAINS = "ConstraintType_LIST_NOT_CONTAINS"
    STRING_CONTAINS = "ConstraintType_STRING_CONTAINS"
    STRING_NOT_CONTAINS = "ConstraintType_STRING_NOT_CONTAINS"


class Constraint:
    pass


class ClassConstraint(Constraint):
    def __init__(self, *, clazz, include_subclasses=False):
        self._clazz = clazz
        self._include_subclasses = include_subclasses
        self._container = None
        self._target_type=None

    def __repr__(self):
        return f"ClassConstraint(target={self._target_type}, class={self._clazz}, include_subclasses={self._include_subclasses})"

    def set_target(self, target_type):
        self._target_type=target_type

    def set_container(self, container: "QueryContainer"):
        self._container = container


class PropertyConstraint(Constraint):

    def __init__(self, *,
                 property,
                 comparator: ConstraintType,
                 value,
                 include_subproperties: bool = False):

        self._property = property
        self._comparator: ConstraintType = comparator
        self._value = value
        self._include_subproperties: bool = include_subproperties
        self._container = None
        self._target_type = None

    def __repr__(self):
        return f"PropertyConstraint(target={self._target_type}, property={self._property}, comparator={self._comparator}, value={self._value}, include_subproperties={self._include_subproperties})"

    def set_target(self, target_type):
        self._target_type=target_type

    def set_container(self, container: "QueryContainer"):
        self._container = container


# to create constraint pass property URI via:

# property uri str
# VITAL_Node.name (class + property ref)
# person123.name (instance + property ref)
# Property_hasName.get_uri() property trait class + get_uri() function


class VectorConstraint(Constraint):
    def __init__(self, *,
                 vector_name,
                 vector_value):
        self._vector_name = vector_name
        self._vector_value = vector_value
        self._container = None
        self._target_type = None

    def __repr__(self):
        return f"VectorConstraint(vector_name={self._vector_name}, vector_value={self._vector_value})"

    def set_target(self, target_type):
        self._target_type=target_type

    def set_container(self, container: "QueryContainer"):
        self._container = container


class ConstraintList:
    def __init__(self):
        self._constraint_list: List[Constraint] = []
        self._container = None

    def node_constraint(self, constraint: Constraint):

        if isinstance(constraint, PropertyConstraint):
            constraint.set_container(self._container)

        if isinstance(constraint, ClassConstraint):
            constraint.set_container(self._container)

        if isinstance(constraint, VectorConstraint):
            constraint.set_container(self._container)

        constraint.set_target(TARGET_TYPE_NODE)
        self._constraint_list.append(constraint)

        return self

    def edge_constraint(self, constraint: Constraint):

        if isinstance(constraint, PropertyConstraint):
            constraint.set_container(self._container)

        if isinstance(constraint, ClassConstraint):
            constraint.set_container(self._container)

        if isinstance(constraint, VectorConstraint):
            constraint.set_container(self._container)

        constraint.set_target(TARGET_TYPE_EDGE)
        self._constraint_list.append(constraint)

        return self

    def set_container(self, container: "QueryContainer"):
        self._container = container


class AndConstraintList(ConstraintList):
    def __repr__(self):
        return f"AndConstraintList(constraints={self._constraint_list})"


class OrConstraintList(ConstraintList):
    def __repr__(self):
        return f"OrConstraintList(constraints={self._constraint_list})"


class ArcList:
    def __init__(self):
        self._arc_list = []
        self._arclist_list = []
        self._container = None

    def arc(self, arc: "Arc"):
        arc.set_container(self._container)
        self._arc_list.append(arc)
        return self

    def arc_list(self, arc_list: "ArcList"):
        arc_list.set_container(self._container)
        self._arclist_list.append(arc_list)
        return self

    def set_container(self, container: "QueryContainer"):
        self._container = container


class AndArcList(ArcList):
    def __repr__(self):
        return f"AndArcList(arcs={self._arc_list})"


class OrArcList(ArcList):
    def __repr__(self):
        return f"OrArcList(arcs={self._arc_list})"


class MetaQLPropertyPath:
    def __init__(self, *,
                 property_uri: str,
                 class_uri: str = None,
                 include_subclasses: bool = False,
                 include_subproperties: bool = False):

        self._property_uri = property_uri
        self._class_uri = class_uri
        self._include_subclasses = include_subclasses
        self._include_subproperties = include_subproperties
        self._container = None

    def __repr__(self):
        return f"MetaQLPropertyPath(property={self._property_uri}, class={self._class_uri}, include_subclasses={self._include_subclasses}, include_subproperties={self._include_subproperties})"


class PropertyPathList:
    def __init__(self):
        self._property_path_list = []
        self._container = None

    def property_path(self, property_path: MetaQLPropertyPath):
        self._property_path_list.append(property_path)
        return self

    def set_container(self, container: "QueryContainer"):
        self._container = container

    def __repr__(self):
        return f"PropertyPathList(property_path_list={self._property_path_list})"


class Bind:
    pass


class NodeBind(Bind):
    def __init__(self, *, name: str):
        self._name = name
        self._container = None

    def set_container(self, container: "QueryContainer"):
        self._container = container

    def __repr__(self):
        return f"NodeBind(name={self._name})"


class EdgeBind(Bind):
    def __init__(self, *, name: str):
        self._name = name
        self._container = None

    def set_container(self, container: "QueryContainer"):
        self._container = container

    def __repr__(self):
        return f"EdgeBind(name={self._name})"


class PathBind(Bind):
    def __init__(self, *, name: str):
        self._name = name
        self._container = None

    def set_container(self, container: "QueryContainer"):
        self._container = container

    def __repr__(self):
        return f"PathBind(name={self._name})"


class SolutionBind(Bind):
    def __init__(self, *, name: str):
        self._name = name
        self._container = None

    def set_container(self, container: "QueryContainer"):
        self._container = container

    def __repr__(self):
        return f"SolutionBind(name={self._name})"


class Arc:
    def __init__(self, *,
                 arc_traverse_type: ARC_TRAVERSE_TYPE = None,
                 arc_direction_type: ARC_DIRECTION_TYPE = None):
        self._is_root = False
        self._sub_arc = None
        self._constraint_list_list = []
        self._arc_list_list = []
        self._property_path_list_list = []
        self._container = None
        self._node_binding = None
        self._edge_binding = None
        self._path_binding = None
        self._solution_binding = None

        self._arc_traverse_type = None
        self._arc_direction_type = None

        if arc_traverse_type:
            self._arc_traverse_type = arc_traverse_type

        if arc_direction_type:
            self._arc_direction_type = arc_direction_type

    def set_is_root(self, is_root: bool):
        self._is_root = is_root

    def constraint_list(self, constraint_list: ConstraintList):
        constraint_list.set_container(self._container)
        self._constraint_list_list.append(constraint_list)
        return self

    def property_path_list(self, property_path_list: PropertyPathList):
        property_path_list.set_container(self._container)
        self._property_path_list_list.append(property_path_list)
        return self

    def node_bind(self, node_binding: NodeBind):
        self._node_binding = node_binding
        return self

    def edge_bind(self, edge_binding: EdgeBind):
        self._edge_binding = edge_binding
        return self

    def path_bind(self, path_binding: PathBind):
        self._path_binding = path_binding
        return self

    def solution_bind(self, solution_binding: SolutionBind):
        self._solution_binding = solution_binding
        return self

    def arc(self, arc: "Arc"):
        arc.set_container(self._container)
        self._sub_arc = arc
        return self

    def arc_list(self, arc_list: ArcList):
        arc_list.set_container(self._container)
        self._arc_list_list.append(arc_list)
        return self

    def set_container(self, container: "QueryContainer"):
        self._container = container

    def __repr__(self):
        return f"Arc(is_root={self._is_root}, sub_arc={self._sub_arc}, constraint_list={self._constraint_list_list}, arc_list={self._arc_list_list}, property_path_list={self._property_path_list_list})"


class Query:
    pass


class SelectQuery(Query):
    def __init__(self, *, offset: int = 0, limit: int = 100,
                 container: "QueryContainer"):
        self._graph_uri_list = []
        self._graph_id_list = []
        self._constraint_list_list = []
        self._offset = offset
        self._limit = limit
        self._container = container

    def constraint_list(self, constraint_list: ConstraintList):
        constraint_list.set_container(self._container)
        self._constraint_list_list.append(constraint_list)
        return self

    def graph_uri(self, graph_uri: str):
        self._graph_uri_list.append(graph_uri)
        return self

    def graph_id(self, graph_id: str):
        self._graph_id_list.append(graph_id)
        return self

    def __repr__(self):
        return f"SelectQuery(graph_id_list={self._graph_id_list}, graph_uri_list={self._graph_uri_list}, constraint_list={self._constraint_list_list}, offset={self._offset}, limit={self._limit})"

    def build(self):
        return self._container.build()


class GraphQuery(Query):
    def __init__(self, *,
                 offset: int = 0,
                 limit: int = 100,
                 resolve_objects: bool = False,
                 container: "QueryContainer"):
        self._graph_uri_list = []
        self._graph_id_list = []
        self._root_arc = None
        self._resolve_objects = resolve_objects
        self._offset = offset
        self._limit = limit
        self._container = container

    def arc(self, arc: Arc):
        arc.set_container(self._container)
        arc.set_is_root(True)
        self._root_arc = arc
        return self

    def graph_uri(self, graph_uri: str):
        self._graph_uri_list.append(graph_uri)
        return self

    def graph_id(self, graph_id: str):
        self._graph_id_list.append(graph_id)
        return self

    def __repr__(self):
        return f"GraphQuery(graph_id_list={self._graph_id_list}, graph_uri_list={self._graph_uri_list}, arc={self._root_arc}, offset={self._offset}, limit={self._limit})"

    def build(self):
        return self._container.build()


class AggregateSelectQuery:
    def __init__(self, *, offset: int = 0, limit: int = 100,
                 container: "QueryContainer"):
        self._graph_uri_list = []
        self._graph_id_list = []
        self._constraint_list_list = []
        self._offset = offset
        self._limit = limit
        self._container = container

    def constraint_list(self, constraint_list: ConstraintList):
        constraint_list.set_container(self._container)
        self._constraint_list_list.append(constraint_list)
        return self

    def graph_uri(self, graph_uri: str):
        self._graph_uri_list.append(graph_uri)
        return self

    def graph_id(self, graph_id: str):
        self._graph_id_list.append(graph_id)
        return self

    def __repr__(self):
        return f"AggregateSelectQuery(graph_id_list={self._graph_id_list}, graph_uri_list={self._graph_uri_list}, constraint_list={self._constraint_list_list}, offset={self._offset}, limit={self._limit})"

    def build(self):
        return self._container.build()


class AggregateGraphQuery:
    def __init__(self, *, offset: int = 0, limit: int = 100,
                 container: "QueryContainer"):
        self._graph_uri_list = []
        self._graph_id_list = []
        self._root_arc = None
        self._offset = offset
        self._limit = limit
        self._container = container

    def graph_uri(self, graph_uri: str):
        self._graph_uri_list.append(graph_uri)
        return self

    def graph_id(self, graph_id: str):
        self._graph_id_list.append(graph_id)
        return self

    def arc(self, arc: Arc):
        arc.set_container(self._container)
        arc.set_is_root(True)
        self._root_arc = arc
        return self

    def __repr__(self):
        return f"AggregateGraphQuery(graph_id_list={self._graph_id_list}, graph_uri_list={self._graph_uri_list}, arc={self._root_arc}, offset={self._offset}, limit={self._limit})"

    def build(self):
        return self._container.build()


class QueryContainer:

    def __init__(self):
        self.query = None

    def build_constraint(self, constraint: Constraint):

        vs = VitalSigns()

        ont_manager = vs.get_ontology_manager()

        if isinstance(constraint, PropertyConstraint):

            # TODO
            # convert property into property uri if necessary
            prop = constraint._property

            property_uri = prop

            prop_info = ont_manager.get_property_info(property_uri)

            prop_class = prop_info.get('prop_class', None)

            property_constraint_type = PropertyDataConstraintUtils.lookup(prop_class)

            comparator = constraint._comparator

            metaql_comparator = ComparatorTypeUtils.lookup_comparator_type(comparator)

            target_type = constraint._target_type

            value = constraint._value

            prop_params = {
                "property_constraint_type": property_constraint_type,
                "property_uri": property_uri,
                "target": target_type,
                "comparator": metaql_comparator,
            }

            PropertyUtils.set_property_param_value(property_constraint_type, value, prop_params)

            pc = MetaQLBuilder.build_property_constraint(**prop_params)

            return pc

        if isinstance(constraint, VectorConstraint):

            vector_name = constraint._vector_name
            vector_value = constraint._vector_value

            prop_params = {
                "vector_name": vector_name,
                "text_constraint_value": vector_value
            }

            pc = MetaQLBuilder.build_vector_constraint(**prop_params)

            return pc

        if isinstance(constraint, ClassConstraint):

            clazz = constraint._clazz
            include_subclasses = constraint._include_subclasses
            target_type = constraint._target_type

            class_constraint_type = NODE_CLASS_CONSTRAINT_TYPE

            # TODO HyperNode, HyperEdge
            if target_type == TARGET_TYPE_NODE:
                class_constraint_type = NODE_CLASS_CONSTRAINT_TYPE

            if target_type == TARGET_TYPE_EDGE:
                class_constraint_type = EDGE_CLASS_CONSTRAINT_TYPE

            cc = MetaQLBuilder.build_class_constraint(
                class_constraint_type=class_constraint_type,
                class_uri=clazz,
                include_subclasses=include_subclasses
            )

            return cc

        return None

    def build_constraint_list_list(self, query_constraint_list_list):

        constraint_list_list = []

        for constraint_list in query_constraint_list_list:

            if isinstance(constraint_list, AndConstraintList):

                cl = []

                for c in constraint_list._constraint_list:

                    metaql_constraint = self.build_constraint(c)

                    if metaql_constraint:
                        cl.append(metaql_constraint)

                cll = MetaQLBuilder.build_constraint_list(
                    constraint_list_type=AND_CONSTRAINT_LIST_TYPE,
                    constraint_list=cl
                )

                constraint_list_list.append(cll)

            if isinstance(constraint_list, OrConstraintList):
                cl = []

                for c in constraint_list._constraint_list:

                    metaql_constraint = self.build_constraint(c)

                    if metaql_constraint:
                        cl.append(metaql_constraint)

                cll = MetaQLBuilder.build_constraint_list(
                    constraint_list_type=OR_CONSTRAINT_LIST_TYPE,
                    constraint_list=cl
                )

                constraint_list_list.append(cll)

        return constraint_list_list

    def build_property_path(self, property_path: MetaQLPropertyPath):

        property_uri = property_path._property_uri
        class_uri = property_path._class_uri
        include_subclasses = property_path._include_subclasses
        include_subproperties = property_path._include_subproperties

        pp = MetaQLBuilder.build_property_path(
            property_uri=property_uri,
            class_uri=class_uri,
            include_subclasses=include_subclasses,
            include_subproperties=include_subproperties
        )

        return pp

    def build_property_path_list_list(self, query_property_path_list_list):

        property_path_list_list = []

        for property_path_list in query_property_path_list_list:

            ppl = []

            for pp in property_path_list._property_path_list:

                metaql_property_path = self.build_property_path(pp)

                if metaql_property_path:
                    ppl.append(metaql_property_path)

            if len(ppl) > 0:
                property_path_list_list.append(ppl)

        return property_path_list_list

    def build_arc(self,
                  in_arc: Arc,
                  in_arclist_list: List[ArcList],
                  in_constraint_list_list,
                  in_property_path_list_list,
                  in_node_binding: NodeBind = None,
                  in_edge_binding: EdgeBind = None,
                  in_path_binding: PathBind = None,
                  in_solution_binding: SolutionBind = None,
                  in_arc_traverse_type: ARC_TRAVERSE_TYPE = None,
                  in_arc_direction_type: ARC_DIRECTION_TYPE = None
                  ):

        if in_arc:
            sub_arc = self.build_arc(
                in_arc._sub_arc,
                in_arc._arc_list_list,
                in_arc._constraint_list_list,
                in_arc._property_path_list_list,
                in_arc._node_binding,
                in_arc._edge_binding,
                in_arc._path_binding,
                in_arc._solution_binding,
                in_arc._arc_traverse_type,
                in_arc._arc_direction_type
            )
        else:
            sub_arc = None

        if in_arclist_list:
            arclist_list = self.build_arclist_list(in_arclist_list)
        else:
            arclist_list = None

        constraint_list_list = self.build_constraint_list_list(in_constraint_list_list)

        property_path_list_list = self.build_property_path_list_list(in_property_path_list_list)

        node_binding=None
        edge_binding=None
        path_binding=None
        solution_binding=None

        if in_node_binding:
            node_binding = MetaQLBuilder.build_node_binding(
                name=in_node_binding._name
            )

        if in_edge_binding:
            edge_binding = MetaQLBuilder.build_edge_binding(
                name=in_edge_binding._name
            )

        if in_path_binding:
            path_binding = MetaQLBuilder.build_path_binding(
                name=in_path_binding._name
            )

        if in_solution_binding:
            solution_binding = MetaQLBuilder.build_solution_binding(
                name=in_solution_binding._name
            )

        arc = MetaQLBuilder.build_arc(
            sub_arc=sub_arc,
            arclist_list=arclist_list,
            constraint_list_list=constraint_list_list,
            property_path_list_list=property_path_list_list,
            node_binding=node_binding,
            edge_binding=edge_binding,
            path_binding=path_binding,
            solution_binding=solution_binding,
            arc_traverse_type=in_arc_traverse_type,
            arc_direction_type=in_arc_direction_type
        )

        return arc

    def build_arclist_list(self, in_arclist_list: List[ArcList]):

        metaql_arclist_list = []

        for in_arc_list in in_arclist_list:

            arc_list_type = AND_ARC_LIST_TYPE

            if isinstance(in_arc_list, AndArcList):
                arc_list_type = AND_ARC_LIST_TYPE

            if isinstance(in_arc_list, OrArcList):
                arc_list_type = OR_ARC_LIST_TYPE

            arc_list = in_arc_list._arc_list

            sub_arclist_list = in_arc_list._arclist_list

            metaql_sub_arclist_list = []

            for sub_arclist in sub_arclist_list:

                sub_metaql_arclist_list = self.build_arclist_list([sub_arclist])
                sub_metaql_arclist = sub_metaql_arclist_list[0]
                metaql_sub_arclist_list.append(sub_metaql_arclist)

            metaql_arc_list = []

            for in_arc in arc_list:

                metaql_arc = self.build_arc(
                    in_arc._sub_arc,
                    in_arc._arc_list_list,
                    in_arc._constraint_list_list,
                    in_arc._property_path_list_list,
                    in_arc._node_binding,
                    in_arc._edge_binding,
                    in_arc._path_binding,
                    in_arc._solution_binding,
                    in_arc._arc_traverse_type,
                    in_arc._arc_direction_type
                )

                metaql_arc_list.append(metaql_arc)

            metaql_arclist = MetaQLBuilder.build_arc_list(
                arc_list_type=arc_list_type,
                arc_list_list=metaql_arc_list,
                arclist_list=metaql_sub_arclist_list)

            if metaql_arclist:
                metaql_arclist_list.append(metaql_arclist)

        return metaql_arclist_list

    def build_root_arc(self,
                       in_arc: Arc,
                       in_arclist_list: List[ArcList],
                       in_constraint_list_list: List[ConstraintList],
                       in_node_binding: NodeBind = None,
                       in_edge_binding: EdgeBind = None,
                       in_path_binding: PathBind = None,
                       in_solution_binding: SolutionBind = None
                       ):

        if in_arc:
            arc = self.build_arc(
                in_arc._sub_arc,
                in_arc._arc_list_list,
                in_arc._constraint_list_list,
                in_arc._property_path_list_list,
                in_arc._node_binding,
                in_arc._edge_binding,
                in_arc._path_binding,
                in_arc._solution_binding
            )
        else:
            arc = None

        if in_arclist_list:
            arclist_list = self.build_arclist_list(in_arclist_list)
        else:
            arclist_list = None

        constraint_list_list = self.build_constraint_list_list(in_constraint_list_list)

        node_binding = None
        edge_binding = None
        path_binding = None
        solution_binding = None

        if in_node_binding:
            node_binding = MetaQLBuilder.build_node_binding(
                name=in_node_binding._name
            )

        if in_edge_binding:
            edge_binding = MetaQLBuilder.build_edge_binding(
                name=in_edge_binding._name
            )

        if in_path_binding:
            path_binding = MetaQLBuilder.build_path_binding(
                name=in_path_binding._name
            )

        if in_solution_binding:
            solution_binding = MetaQLBuilder.build_solution_binding(
                name=in_solution_binding._name
            )

        arc_root = MetaQLBuilder.build_root_arc(
            arc=arc,
            arclist_list=arclist_list,
            constraint_list_list=constraint_list_list,
            node_binding=node_binding,
            edge_binding=edge_binding,
            path_binding=path_binding,
            solution_binding=solution_binding
        )

        return arc_root

    def build(self):

        if isinstance(self.query, SelectQuery):

            # print(f"Build Query: {self.query}")

            # selects only have constraint list
            root_arc = self.build_root_arc(
                None,
                None,
                self.query._constraint_list_list,
                None,
                None,
                None,
                None
            )

            sq = MetaQLBuilder.build_metaql_query(
                metaql_query_type=METAQL_SELECT_QUERY,
                graph_uri_list=self.query._graph_uri_list,
                graph_id_list=self.query._graph_id_list,
                limit=self.query._limit,
                offset=self.query._offset,
                root_arc=root_arc
            )

            return sq

        if isinstance(self.query, GraphQuery):

            # print(f"Build Query: {self.query}")

            root_arc = self.build_root_arc(
                self.query._root_arc._sub_arc,
                self.query._root_arc._arc_list_list,
                self.query._root_arc._constraint_list_list,
                self.query._root_arc._node_binding,
                self.query._root_arc._edge_binding,
                self.query._root_arc._path_binding,
                self.query._root_arc._solution_binding
            )

            gq = MetaQLBuilder.build_metaql_query(
                metaql_query_type=METAQL_GRAPH_QUERY,
                graph_uri_list=self.query._graph_uri_list,
                graph_id_list=self.query._graph_id_list,
                resolve_objects=self.query._resolve_objects,
                limit=self.query._limit,
                offset=self.query._offset,
                root_arc=root_arc
            )

            return gq

        if isinstance(self.query, AggregateSelectQuery):

            # selects only have constraint lists
            root_arc = self.build_root_arc(
                None,
                None,
                self.query._constraint_list_list,
                None,
                None,
                None,
                None
            )

            asq = MetaQLBuilder.build_metaql_query(
                metaql_query_type=METAQL_AGGREGATE_SELECT_QUERY,
                graph_uri_list=self.query._graph_uri_list,
                graph_id_list=self.query._graph_id_list,
                limit=self.query._limit,
                offset=self.query._offset,
                root_arc=root_arc
            )

            return asq

        if isinstance(self.query, AggregateGraphQuery):

            root_arc = self.build_root_arc(
                self.query._root_arc._sub_arc,
                self.query._root_arc._arc_list_list,
                self.query._root_arc._constraint_list_list,
                self.query._root_arc._node_binding,
                self.query._root_arc._edge_binding,
                self.query._root_arc._path_binding,
                self.query._root_arc._solution_binding
            )

            agq = MetaQLBuilder.build_metaql_query(
                metaql_query_type=METAQL_AGGREGATE_GRAPH_QUERY,
                graph_uri_list=self.query._graph_uri_list,
                graph_id_list=self.query._graph_id_list,
                limit=self.query._limit,
                offset=self.query._offset,
                root_arc=root_arc
            )

            return agq

        return None

class QueryBuilder:

    @classmethod
    def select_query(cls, *,
                     offset: int = 0,
                     limit: int = 100):

        query_container = QueryContainer()

        select_query = SelectQuery(
            offset=offset,
            limit=limit,
            container=query_container)

        query_container.query = select_query

        return select_query

    @classmethod
    def graph_query(cls, *,
                    offset: int = 0,
                    limit: int = 100,
                    resolve_objects: bool = False):

        query_container = QueryContainer()

        graph_query = GraphQuery(
            offset=offset,
            limit=limit,
            resolve_objects=resolve_objects,
            container=query_container)

        query_container.query = graph_query

        return graph_query

