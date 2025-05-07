from datetime import datetime
from typing import List, Dict, Callable, Any, Union

from vital_ai_vitalsigns.metaql.aggregate.metaql_aggregate import MetaQLAggregate
from vital_ai_vitalsigns.metaql.arc.metaql_arc import Arc, ArcRoot, ARC_TYPE_ARC_ROOT, ARC_TYPE_ARC, \
    ARC_TRAVERSE_TYPE_EDGE, ARC_DIRECTION_TYPE_FORWARD, MetaQLPropertyPath, MetaQLArc, ARC_TRAVERSE_TYPE, \
    ARC_DIRECTION_TYPE, NodeArcBinding, EdgeArcBinding, PathArcBinding, SolutionArcBinding
from vital_ai_vitalsigns.metaql.arc_list.metaql_arc_list import MetaQLArcList, ARC_LIST_TYPE, AND_ARC_LIST_TYPE, \
    AndArcList, OrArcList, OR_ARC_LIST_TYPE
from vital_ai_vitalsigns.metaql.constraint.metaql_class_constraint import NODE_CLASS_CONSTRAINT_TYPE, ClassConstraint, \
    NodeConstraint, EDGE_CLASS_CONSTRAINT_TYPE, EdgeConstraint, HYPER_NODE_CLASS_CONSTRAINT_TYPE, HyperNodeConstraint, \
    HyperEdgeConstraint, HYPER_EDGE_CLASS_CONSTRAINT_TYPE
from vital_ai_vitalsigns.metaql.constraint.metaql_constraint import MetaQLConstraint, CLASS_CONSTRAINT_TYPE, \
    VECTOR_CONSTRAINT_TYPE, PROPERTY_CONSTRAINT_TYPE, COMPARATOR_TYPE
from vital_ai_vitalsigns.metaql.constraint.metaql_property_constraint import STRING_PROPERTY_DATA_CONSTRAINT_TYPE, \
    StringPropertyConstraint, EXISTS_PROPERTY_DATA_CONSTRAINT_TYPE, NOT_EXISTS_PROPERTY_DATA_CONSTRAINT_TYPE, \
    NotExistsPropertyConstraint, ExistsPropertyConstraint, BOOLEAN_PROPERTY_DATA_CONSTRAINT_TYPE, \
    BooleanPropertyConstraint, \
    FloatPropertyConstraint, FLOAT_PROPERTY_DATA_CONSTRAINT_TYPE, IntegerPropertyConstraint, \
    INTEGER_PROPERTY_DATA_CONSTRAINT_TYPE, LONG_PROPERTY_DATA_CONSTRAINT_TYPE, LongPropertyConstraint, \
    DATETIME_PROPERTY_DATA_CONSTRAINT_TYPE, DateTimePropertyConstraint, DOUBLE_PROPERTY_DATA_CONSTRAINT_TYPE, \
    DoublePropertyConstraint, TRUTH_PROPERTY_DATA_CONSTRAINT_TYPE, TruthPropertyConstraint, \
    GEOLOCATION_PROPERTY_DATA_CONSTRAINT_TYPE, GeoLocationPropertyConstraint, OtherPropertyConstraint, \
    OTHER_PROPERTY_DATA_CONSTRAINT_TYPE, TARGET_TYPE, TRUTH_TYPE, URI_PROPERTY_DATA_CONSTRAINT_TYPE, \
    URIPropertyConstraint
from vital_ai_vitalsigns.metaql.constraint.metaql_vector_constraint import VECTOR_COMPARATOR_TYPE, \
    VECTOR_COMPARATOR_TYPE_NEAR_TO, VECTOR_CONSTRAINT_TYPE_VECTOR, VECTOR_CONSTRAINT_TYPE_TEXT, VectorConstraint, \
    VectorConstraintVectorValue, VectorConstraintTextValue
from vital_ai_vitalsigns.metaql.constraint_list.metaql_constraint_list import MetaQLConstraintList, \
    CONSTRAINT_LIST_TYPE, AND_CONSTRAINT_LIST_TYPE, AndConstraintList, OR_CONSTRAINT_LIST_TYPE, OrConstraintList
from vital_ai_vitalsigns.metaql.metaql_request import MetaQLRequest
from vital_ai_vitalsigns.metaql.metaql_query import MetaQLQuery, METAQL_QUERY_TYPE, METAQL_SELECT_QUERY, SelectQuery, \
    METAQL_GRAPH_QUERY, GraphQuery, METAQL_AGGREGATE_SELECT_QUERY, AggregateSelectQuery, METAQL_AGGREGATE_GRAPH_QUERY, \
    AggregateGraphQuery
from vital_ai_vitalsigns.metaql.metaql_response import MetaQLResponse
from vital_ai_vitalsigns.metaql.metaql_result_element import MetaQLResultElement
from vital_ai_vitalsigns.metaql.metaql_result_list import MetaQLResultList
from vital_ai_vitalsigns.metaql.metaql_status import MetaQLStatus, STATUS_TYPE
from vital_ai_vitalsigns.model.GraphObject import GraphObject


class MetaQLBuilder:

    @classmethod
    def build_metaql_request(cls, *,
                             account_uri: str = "",
                             account_id: str = "",
                             login_uri: str = "",
                             jwt_str: str = "",
                             metaql_query: MetaQLQuery = None) -> MetaQLRequest:

        if metaql_query is None:
            # exception
            return None

        metaql_request = MetaQLRequest(
            metaql_class = "MetaQLRequest",
            account_uri=account_uri,
            account_id=account_id,
            login_uri=login_uri,
            jwt_str=jwt_str,
            metaql_query=metaql_query)

        return metaql_request

    @classmethod
    def build_metaql_query(cls, *,
                           metaql_query_type: METAQL_QUERY_TYPE = METAQL_SELECT_QUERY,
                           graph_uri_list: List[str] | None = None,
                           graph_id_list: List[str] | None = None,
                           root_arc: Arc | None = None,
                           offset: int = 0,
                           limit: int = 100,
                           resolve_objects: bool = False,
                           aggregate: MetaQLAggregate | None = None) -> SelectQuery | GraphQuery | AggregateSelectQuery | AggregateGraphQuery | None:

        if not graph_uri_list:
            graph_uri_list = []

        if not graph_id_list:
            graph_id_list = []

        if not root_arc:
            # exception
            return None

        metaql_query = None

        if metaql_query_type == METAQL_SELECT_QUERY:

            if aggregate is not None:
                # exception
                pass

            metaql_query = SelectQuery(
                metaql_class="SelectQuery",
                query_type=METAQL_SELECT_QUERY,
                graph_uri_list=graph_uri_list,
                graph_id_list=graph_id_list,
                offset=offset,
                limit=limit,
                arc=root_arc
            )

        if metaql_query_type == METAQL_GRAPH_QUERY:

            if aggregate is not None:
                # exception
                pass

            metaql_query = GraphQuery(
                metaql_class="GraphQuery",
                query_type=METAQL_GRAPH_QUERY,
                graph_uri_list=graph_uri_list,
                graph_id_list=graph_id_list,
                resolve_objects=resolve_objects,
                offset=offset,
                limit=limit,
                arc=root_arc
            )

        if metaql_query_type == METAQL_AGGREGATE_SELECT_QUERY:

            if aggregate is None:
                # exception
                pass

            metaql_query = AggregateSelectQuery(
                metaql_class="AggregateSelectQuery",
                query_type=METAQL_AGGREGATE_SELECT_QUERY,
                graph_uri_list=graph_uri_list,
                graph_id_list=graph_id_list,
                offset=0,
                limit=1,
                arc=root_arc,
                aggregate=aggregate
            )

        if metaql_query_type == METAQL_AGGREGATE_GRAPH_QUERY:

            if aggregate is None:
                # exception
                pass

            metaql_query = AggregateGraphQuery(
                metaql_class="AggregateGraphQuery",
                query_type=METAQL_AGGREGATE_GRAPH_QUERY,
                graph_uri_list=graph_uri_list,
                graph_id_list=graph_id_list,
                resolve_objects=False,
                offset=0,
                limit=1,
                arc=root_arc,
                aggregate=aggregate
            )

        if metaql_query is None:
            # exception, no query built
            return None

        return metaql_query

    @classmethod
    def build_property_path(cls, *,
                            class_uri: str | None = None,
                            include_subclasses: bool | None,
                            property_uri: str | None,
                            include_subproperties: bool | None) -> MetaQLPropertyPath | None:

        if property_uri is None:
            # exception
            return None

        property_path = MetaQLPropertyPath(
            metaql_class = "MetaQLPropertyPath",
            class_uri=class_uri,
            include_subclasses=include_subclasses,
            property_uri=property_uri,
            include_subproperties=include_subproperties
        )

        return property_path

    @classmethod
    def build_node_binding(cls, *, name: str):

        # print(f"build_node_binding {name}")

        node_binding = NodeArcBinding(
            metaql_class="NodeArcBinding",
            binding=name
        )

        return node_binding

    @classmethod
    def build_edge_binding(cls, *, name: str):

        edge_binding = EdgeArcBinding(
            metaql_class="EdgeArcBinding",
            binding=name
        )

        return edge_binding

    @classmethod
    def build_path_binding(cls, *, name: str):

        path_binding = PathArcBinding(
            metaql_class="PathArcBinding",
            binding=name
        )

        return path_binding

    @classmethod
    def build_solution_binding(cls, *, name: str):

        solution_binding = SolutionArcBinding(
            metaql_class="SolutionArcBinding",
            binding=name
        )

        return solution_binding

    @classmethod
    def build_root_arc(cls, *,
                       arc: Arc | None = None,
                       node_binding: NodeArcBinding | None = None,
                       edge_binding: EdgeArcBinding | None = None,
                       path_binding: PathArcBinding | None = None,
                       solution_binding: SolutionArcBinding | None = None,
                       arclist_list: List[MetaQLArcList] | None = None,
                       constraint_list_list: List[MetaQLConstraintList] | None = None) -> ArcRoot | None:

        if arclist_list is None:
            arclist_list = []

        if constraint_list_list is None or len(constraint_list_list) == 0:
            # exception
            return None

        arc_root = ArcRoot(
            metaql_class="ArcRoot",
            arc_type=ARC_TYPE_ARC_ROOT,
            arc_traverse_type=ARC_TRAVERSE_TYPE_EDGE,
            arc_direction_type=ARC_DIRECTION_TYPE_FORWARD,
            node_binding=node_binding,
            edge_binding=edge_binding,
            path_binding=path_binding,
            solution_binding=solution_binding,
            property_path_list_list=[],
            arc=arc,
            arclist_list=arclist_list,
            constraint_list_list=constraint_list_list
        )

        return arc_root

    @classmethod
    def build_arc(cls, *,
                  sub_arc: Arc = None,
                  arc_traverse_type: ARC_TRAVERSE_TYPE | None = ARC_TRAVERSE_TYPE_EDGE,
                  arc_direction_type: ARC_DIRECTION_TYPE | None = ARC_DIRECTION_TYPE_FORWARD,
                  node_binding: NodeArcBinding | None = None,
                  edge_binding: EdgeArcBinding | None = None,
                  path_binding: PathArcBinding | None = None,
                  solution_binding: SolutionArcBinding | None = None,
                  arclist_list: List[MetaQLArcList] = None,
                  constraint_list_list: List[MetaQLConstraintList] = None,
                  property_path_list_list: List[List[MetaQLPropertyPath]] = None) -> Arc | None:

        if arc_traverse_type is None:
            arc_traverse_type = ARC_TRAVERSE_TYPE_EDGE

        if arc_direction_type is None:
            arc_direction_type = ARC_DIRECTION_TYPE_FORWARD

        if arclist_list is None:
            arclist_list = []

        if property_path_list_list is None:
            property_path_list = []

        if constraint_list_list is None or len(constraint_list_list) == 0:
            # exception
            pass

        # print(f"build_arc node_binding: {node_binding}")

        arc = Arc(
            metaql_class="Arc",
            arc_type=ARC_TYPE_ARC,
            arc_traverse_type=arc_traverse_type,
            arc_direction_type=arc_direction_type,
            node_binding=node_binding,
            edge_binding=edge_binding,
            path_binding=path_binding,
            solution_binding=solution_binding,
            property_path_list_list=property_path_list_list,
            arc=sub_arc,
            arclist_list=arclist_list,
            constraint_list_list=constraint_list_list
        )

        return arc

    @classmethod
    def build_arc_list(cls, *,
                       arc_list_type: ARC_LIST_TYPE = AND_ARC_LIST_TYPE,
                       arc_list_list: List[MetaQLArc] = None,
                       arclist_list: List[MetaQLArcList] = None) -> MetaQLArcList | None:

        arc_list = None

        if arc_list_list is None and arclist_list is None:
            # this should be an exception
            pass

        if arc_list_list is None:
            arc_list_list = []

        if arclist_list is None:
            arclist_list = []

        if arc_list_type == AND_ARC_LIST_TYPE:
            arc_list = AndArcList(
                metaql_class="AndArcList",
                arc_list_type=AND_ARC_LIST_TYPE,
                arc_list=arc_list_list,
                arclist_list=arclist_list
            )

        if arc_list_type == OR_ARC_LIST_TYPE:
            arc_list = OrArcList(
                metaql_class="OrArcList",
                arc_list_type=OR_ARC_LIST_TYPE,
                arc_list=arc_list_list,
                arclist_list=arclist_list
            )

        return arc_list

    @classmethod
    def build_constraint_list(cls, *,
                              constraint_list_type: CONSTRAINT_LIST_TYPE = AND_CONSTRAINT_LIST_TYPE,
                              constraint_list: List[MetaQLConstraint] = None) -> MetaQLConstraintList:

        if constraint_list is None:
            # exception
            constraint_list = []

        if constraint_list_type == AND_CONSTRAINT_LIST_TYPE:

            constraint_list = AndConstraintList(
                metaql_class="AndConstraintList",
                constraint_list_type=AND_CONSTRAINT_LIST_TYPE,
                constraint_list=constraint_list
            )

        if constraint_list_type == OR_CONSTRAINT_LIST_TYPE:
            constraint_list = OrConstraintList(
                metaql_class="OrConstraintList",
                constraint_list_type=OR_CONSTRAINT_LIST_TYPE,
                constraint_list=constraint_list
            )

        return constraint_list

    @classmethod
    def build_class_constraint(cls, *,
                               class_constraint_type: CLASS_CONSTRAINT_TYPE = None,
                               class_uri: str,
                               include_subclasses: bool = False):

        if class_uri is None:
            # exception
            pass

        if class_constraint_type is None:
            # exception
            pass

        class_constraint = None

        if class_constraint_type == NODE_CLASS_CONSTRAINT_TYPE:
            class_constraint = NodeConstraint(
                metaql_class="NodeConstraint",
                class_constraint_type=NODE_CLASS_CONSTRAINT_TYPE,
                class_uri=class_uri,
                include_subclasses=include_subclasses,
                constraint_type=CLASS_CONSTRAINT_TYPE
            )

        if class_constraint_type == EDGE_CLASS_CONSTRAINT_TYPE:
            class_constraint = EdgeConstraint(
                metaql_class="EdgeConstraint",
                class_constraint_type=EDGE_CLASS_CONSTRAINT_TYPE,
                class_uri=class_uri,
                include_subclasses=include_subclasses,
                constraint_type=CLASS_CONSTRAINT_TYPE
            )

        if class_constraint_type == HYPER_NODE_CLASS_CONSTRAINT_TYPE:
            class_constraint = HyperNodeConstraint(
                metaql_class="HyperNodeConstraint",
                class_constraint_type=HYPER_NODE_CLASS_CONSTRAINT_TYPE,
                class_uri=class_uri,
                include_subclasses=include_subclasses,
                constraint_type=CLASS_CONSTRAINT_TYPE
            )

        if class_constraint_type == HYPER_EDGE_CLASS_CONSTRAINT_TYPE:
            class_constraint = HyperEdgeConstraint(
                metaql_class="HyperEdgeConstraint",
                class_constraint_type=HYPER_EDGE_CLASS_CONSTRAINT_TYPE,
                class_uri=class_uri,
                include_subclasses=include_subclasses,
                constraint_type=CLASS_CONSTRAINT_TYPE
            )

        return class_constraint

    @classmethod
    def build_vector_constraint(cls, *,
                                vector_constraint_type: VECTOR_CONSTRAINT_TYPE = VECTOR_CONSTRAINT_TYPE_TEXT,
                                vector_comparator_type: VECTOR_COMPARATOR_TYPE = VECTOR_COMPARATOR_TYPE_NEAR_TO,
                                class_uri: str | None = None,
                                vector_name: str | None = None,
                                text_constraint_value: str | None = None,
                                vector_constraint_value: List[float] | None = None

                                ) -> VectorConstraintVectorValue | VectorConstraintTextValue | None:

        metaql_vector_constraint = None

        if vector_constraint_type is None:
            # exception
            return None

        if vector_comparator_type is None:
            # exception
            return None

        if vector_constraint_type == VECTOR_CONSTRAINT_TYPE_VECTOR:
            metaql_vector_constraint = VectorConstraintVectorValue(
              metaql_class="VectorConstraintVectorValue",
              vector_constraint_type=vector_constraint_type,
              vector_comparator_type=vector_comparator_type,
              class_uri=class_uri,
              vector_name=vector_name,
              vector_constraint_value=vector_constraint_value,
              constraint_type=VECTOR_CONSTRAINT_TYPE
            )

        if vector_constraint_type == VECTOR_CONSTRAINT_TYPE_TEXT:
            metaql_vector_constraint = VectorConstraintTextValue(
                metaql_class="VectorConstraintTextValue",
                vector_constraint_type=vector_constraint_type,
                vector_comparator_type=vector_comparator_type,
                class_uri=class_uri,
                vector_name=vector_name,
                text_constraint_value=text_constraint_value,
                constraint_type=VECTOR_CONSTRAINT_TYPE
            )

        return metaql_vector_constraint

    @classmethod
    def build_property_constraint(cls, *,
                                  property_constraint_type: PROPERTY_CONSTRAINT_TYPE,
                                  target: TARGET_TYPE,
                                  property_uri: str = None,
                                  include_subproperties: bool = False,
                                  comparator: COMPARATOR_TYPE,
                                  string_value: str = None,
                                  boolean_value: bool = None,
                                  float_value: float = None,
                                  integer_value: int = None,
                                  long_value: int = None,
                                  double_value: float = None,
                                  other_value: str = None,
                                  geolocation_value: str = None,
                                  truth_value: TRUTH_TYPE = None,
                                  datetime_value: datetime = None,
                                  uri_value: str = None,
                                  ):

        property_constraint = None

        # look up value
        is_multi_value = False

        if property_constraint_type is None:
            # exception
            return None

        if property_constraint_type == EXISTS_PROPERTY_DATA_CONSTRAINT_TYPE:

            property_constraint = ExistsPropertyConstraint(
                metaql_class="ExistsPropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE
            )

        if property_constraint_type == NOT_EXISTS_PROPERTY_DATA_CONSTRAINT_TYPE:

            property_constraint = NotExistsPropertyConstraint(
                metaql_class="NotExistsPropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE
            )

        if property_constraint_type == STRING_PROPERTY_DATA_CONSTRAINT_TYPE:

            property_constraint = StringPropertyConstraint(
                metaql_class="StringPropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE,
                string_value=string_value
            )

        if property_constraint_type == BOOLEAN_PROPERTY_DATA_CONSTRAINT_TYPE:
            property_constraint = BooleanPropertyConstraint(
                metaql_class="BooleanPropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE,
                boolean_value=boolean_value
            )

        if property_constraint_type == FLOAT_PROPERTY_DATA_CONSTRAINT_TYPE:
            property_constraint = FloatPropertyConstraint(
                metaql_class="FloatPropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE,
                float_value=float_value
            )

        if property_constraint_type == INTEGER_PROPERTY_DATA_CONSTRAINT_TYPE:
            property_constraint = IntegerPropertyConstraint(
                metaql_class="IntegerPropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE,
                integer_value=integer_value
            )

        if property_constraint_type == LONG_PROPERTY_DATA_CONSTRAINT_TYPE:
            property_constraint = LongPropertyConstraint(
                metaql_class="LongPropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE,
                long_value=long_value)

        if property_constraint_type == DATETIME_PROPERTY_DATA_CONSTRAINT_TYPE:
            property_constraint = DateTimePropertyConstraint(
                metaql_class="DateTimePropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE,
                datetime_value=datetime_value
            )

        if property_constraint_type == DOUBLE_PROPERTY_DATA_CONSTRAINT_TYPE:
            property_constraint = DoublePropertyConstraint(
                metaql_class="DoublePropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE,
                double_value=double_value
            )

        if property_constraint_type == TRUTH_PROPERTY_DATA_CONSTRAINT_TYPE:
            property_constraint = TruthPropertyConstraint(
                metaql_class="TruthPropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE,
                truth_value=truth_value
            )

        if property_constraint_type == GEOLOCATION_PROPERTY_DATA_CONSTRAINT_TYPE:
            property_constraint = GeoLocationPropertyConstraint(
                metaql_class="GeoLocationPropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE,
                geolocation_value=geolocation_value
            )

        if property_constraint_type == OTHER_PROPERTY_DATA_CONSTRAINT_TYPE:
            property_constraint = OtherPropertyConstraint(
                metaql_class="OtherPropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE,
                other_value=other_value
            )

        if property_constraint_type == URI_PROPERTY_DATA_CONSTRAINT_TYPE:
            property_constraint = URIPropertyConstraint(
                metaql_class="URIPropertyConstraint",
                property_constraint_type=property_constraint_type,
                target=target,
                property_uri=property_uri,
                comparator=comparator,
                include_subproperties=include_subproperties,
                is_multi_value=is_multi_value,
                constraint_type=PROPERTY_CONSTRAINT_TYPE,
                uri_value=uri_value
            )


        return property_constraint

    @classmethod
    def build_response(cls, *,
                       result_status: MetaQLStatus,
                       result_list: MetaQLResultList = None):

        response = MetaQLResponse(
            metaql_class="MetaQLResponse",
            result_status=result_status,
            result_list=result_list
        )

        return response

    @classmethod
    def build_status(cls, *,
                     status_type: STATUS_TYPE = "OK_STATUS_TYPE",
                     status_code: int = 0,
                     status_message: str = None):

        status = MetaQLStatus(
            metaql_class="MetaQLStatus",
            status_type=status_type,
            status_code=status_code,
            status_message=status_message
        )

        return status

    @classmethod
    def build_result_list(cls, *,
                          offset: int,
                          limit: int,
                          result_count: int,
                          total_result_count: int,
                          binding_list: list[str] = None,
                          result_list: List[MetaQLResultElement],
                          result_object_list: List[GraphObject] = None):

        result_list = MetaQLResultList(
            metaql_class="MetaQLResultList",
            offset=offset,
            limit=limit,
            result_count=result_count,
            total_result_count=total_result_count,
            binding_list=binding_list,
            result_list=result_list,
            result_object_list=result_object_list
        )

        return result_list

    @classmethod
    def build_result_element(cls, *, graph_object: GraphObject, score: float = 1.0):

        result_element = MetaQLResultElement(
            metaql_class="MetaQLResultElement",
            graph_object=graph_object,
            score=score
        )

        return result_element

