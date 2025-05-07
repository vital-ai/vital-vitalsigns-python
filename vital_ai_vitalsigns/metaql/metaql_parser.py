import json

from vital_ai_vitalsigns.metaql.arc_list.metaql_arc_list import AND_ARC_LIST_TYPE, OR_ARC_LIST_TYPE
from vital_ai_vitalsigns.metaql.constraint.metaql_class_constraint import NodeConstraint, NODE_CLASS_CONSTRAINT_TYPE, \
    EDGE_CLASS_CONSTRAINT_TYPE, HYPER_NODE_CLASS_CONSTRAINT_TYPE, HYPER_EDGE_CLASS_CONSTRAINT_TYPE
from vital_ai_vitalsigns.metaql.constraint.metaql_vector_constraint import VECTOR_CONSTRAINT_TYPE_VECTOR, \
    VECTOR_CONSTRAINT_TYPE_TEXT
from vital_ai_vitalsigns.metaql.constraint_list.metaql_constraint_list import AND_CONSTRAINT_LIST_TYPE, \
    OR_CONSTRAINT_LIST_TYPE
from vital_ai_vitalsigns.metaql.metaql_builder import MetaQLBuilder
from vital_ai_vitalsigns.metaql.metaql_query import SelectQuery, AggregateGraphQuery, AggregateSelectQuery, GraphQuery
from vital_ai_vitalsigns.metaql.metaql_status import MetaQLStatus
from vital_ai_vitalsigns.model.GraphObject import GraphObject


class MetaQLParser:

    @classmethod
    def parse_metaql_request_json(cls, metaql_request_json: str) -> SelectQuery | GraphQuery | AggregateSelectQuery | AggregateGraphQuery | None:

        metaql_request_dict = json.loads(metaql_request_json)

        metaql_class = metaql_request_dict.get('metaql_class', None)

        if metaql_class == 'MetaQLRequest':

            account_uri = metaql_request_dict.get('account_uri', None)
            account_id = metaql_request_dict.get('account_id', None)
            login_uri = metaql_request_dict.get('login_uri', None)
            jwt_str = metaql_request_dict.get('jwt_str', None)

            metaql_query_dict = metaql_request_dict.get('metaql_query', None)

            if metaql_query_dict:

                metaql_query = cls.parse_metaql_dict(metaql_query_dict)

                if cls._check_query(metaql_query):
                    return metaql_query

        return None

    @classmethod
    def _check_query(cls, metaql_query) -> bool:

        if isinstance(metaql_query, dict):

            metaql_class = metaql_query.get('metaql_class', None)

            if metaql_class == 'SelectQuery':
                return True

            if metaql_class == 'GraphQuery':
                return True

            if metaql_class == 'AggregateSelectQuery':
                return True

            if metaql_class == 'AggregateGraphQuery':
                return True

        return False

    @classmethod
    def parse_metaql_dict(cls, metaql_dict) -> dict | None:

        metaql_class = metaql_dict.get('metaql_class', None)

        # print(f"metaql_class: {metaql_class}")

        if metaql_class is None:
            return None

        parse_dict = dict()

        for k, v in metaql_dict.items():

            if isinstance(v, dict):
                v_dict = cls.parse_metaql_dict(v)
                parse_dict[k] = v_dict

            elif isinstance(v, list):
                parse_list = []
                for e in v:
                    if isinstance(e, dict):
                        e_dict = cls.parse_metaql_dict(e)
                        parse_list.append(e_dict)
                    else:
                        parse_list.append(e)
                parse_dict[k] = parse_list

            else:
                if k != 'metaql_class':
                    parse_dict[k] = v

        if metaql_class == 'SelectQuery':

            params_dict = {}

            params_dict['metaql_query_type'] = parse_dict.get('query_type', None)
            params_dict['graph_uri_list'] = parse_dict.get('graph_uri_list', None)
            params_dict['graph_id_list'] = parse_dict.get('graph_id_list', None)

            params_dict['root_arc'] = parse_dict.get('arc', None)
            params_dict['offset'] = parse_dict.get('offset', 0)
            params_dict['limit'] = parse_dict.get('limit', 10)

            select_query = MetaQLBuilder.build_metaql_query(**params_dict)
            return select_query

        if metaql_class == 'GraphQuery':
            params_dict = {}

            params_dict['metaql_query_type'] = parse_dict.get('query_type', None)
            params_dict['graph_uri_list'] = parse_dict.get('graph_uri_list', None)
            params_dict['graph_id_list'] = parse_dict.get('graph_id_list', None)

            params_dict['root_arc'] = parse_dict.get('arc', None)
            params_dict['offset'] = parse_dict.get('offset', 0)
            params_dict['limit'] = parse_dict.get('limit', 10)
            params_dict['resolve_objects'] = parse_dict.get('resolve_objects', False)


            graph_query = MetaQLBuilder.build_metaql_query(**params_dict)

            return graph_query

        if metaql_class == 'AggregateSelectQuery':

            params_dict = {}

            params_dict['metaql_query_type'] = parse_dict.get('query_type', None)
            params_dict['graph_uri_list'] = parse_dict.get('graph_uri_list', None)
            params_dict['graph_id_list'] = parse_dict.get('graph_id_list', None)

            params_dict['root_arc'] = parse_dict.get('arc', None)
            params_dict['offset'] = parse_dict.get('offset', 0)
            params_dict['limit'] = parse_dict.get('limit', 1)

            params_dict['aggregate'] = parse_dict.get('aggregate', None)

            aggregate_select_query = MetaQLBuilder.build_metaql_query(**params_dict)
            return aggregate_select_query

        if metaql_class == 'AggregateGraphQuery':
            params_dict = {}

            params_dict['metaql_query_type'] = parse_dict.get('query_type', None)
            params_dict['graph_uri_list'] = parse_dict.get('graph_uri_list', None)
            params_dict['graph_id_list'] = parse_dict.get('graph_id_list', None)

            params_dict['root_arc'] = parse_dict.get('arc', None)
            params_dict['offset'] = parse_dict.get('offset', 0)
            params_dict['limit'] = parse_dict.get('limit', 1)
            params_dict['resolve_objects'] = parse_dict.get('resolve_objects', False)

            params_dict['aggregate'] = parse_dict.get('aggregate', None)

            aggregate_graph_query = MetaQLBuilder.build_metaql_query(**params_dict)
            return aggregate_graph_query

        if metaql_class == 'MetaQLPropertyPath':

            params_dict = {}

            params_dict['class_uri'] = parse_dict.get('class_uri', None)
            params_dict['include_subclasses'] = parse_dict.get('include_subclasses', None)
            params_dict['property_uri'] = parse_dict.get('property_uri', None)
            params_dict['include_subproperties'] = parse_dict.get('include_subproperties', None)

            property_path = MetaQLBuilder.build_property_path(**params_dict)

            return property_path

        if metaql_class == 'NodeArcBinding':

            params_dict = {}

            # print(f"parse_metaql_dict: NodeArcBinding: {parse_dict}")


            # this path seems to just be used by the arc root base
            # and node arc binding has a "binding" value here
            # whereas in the non-root cases it's a pass-thru?
            # NodeBind uses "name" whereas node arc binding uses "binding"

            # params_dict['name'] = parse_dict.get('name', None)

            # in arc list it seems the value from the source parse is used directly
            # and not by parsing the components recursively
            params_dict['name'] = parse_dict.get('binding', None)

            # print(f"parse_metaql_dict: NodeArcBinding Params Dict: {params_dict}")

            node_binding = MetaQLBuilder.build_node_binding(**params_dict)

            return node_binding

        if metaql_class == 'EdgeArcBinding':

            params_dict = {}

            params_dict['name'] = parse_dict.get('name', None)

            edge_binding = MetaQLBuilder.build_edge_binding(**params_dict)

            return edge_binding

        if metaql_class == 'PathArcBinding':

            params_dict = {}

            params_dict['name'] = parse_dict.get('name', None)

            path_binding = MetaQLBuilder.build_path_binding(**params_dict)

            return path_binding

        if metaql_class == 'SolutionArcBinding':

            params_dict = {}

            params_dict['name'] = parse_dict.get('name', None)

            solution_binding = MetaQLBuilder.build_solution_binding(**params_dict)

            return solution_binding

        if metaql_class == 'ArcRoot':

            params_dict = {}

            params_dict['arc'] = parse_dict.get('arc', None)

            arc_list = parse_dict.get('arc_list', None)

            # are we using the 'arc_list' key?
            # once the builder builds it is it always a list-list?
            # or a arc_list or arclist_list but not both?
            # should the arc_list case be wrapped in an AND to be consistent?

            # TODO Testing this
            # params_dict['arclist_list'] = parse_dict.get('arclist_list', None)

            if arc_list is not None:
                params_dict['arclist_list'] = parse_dict.get('arc_list', None)
            else:
                params_dict['arclist_list'] = parse_dict.get('arclist_list', None)

            # print(f"ArcRoot Node Binding: {parse_dict.get('node_binding', None)}")

            params_dict['constraint_list_list'] = parse_dict.get('constraint_list_list', None)

            params_dict['node_binding'] = parse_dict.get('node_binding', None)
            params_dict['edge_binding'] = parse_dict.get('edge_binding', None)
            params_dict['path_binding'] = parse_dict.get('path_binding', None)
            params_dict['solution_binding'] = parse_dict.get('solution_binding', None)

            root_arc = MetaQLBuilder.build_root_arc(**params_dict)

            return root_arc

        if metaql_class == 'Arc':

            params_dict = {}

            params_dict['sub_arc'] = parse_dict.get('arc', None)

            arc_list = parse_dict.get('arc_list', None)

            # are we using the 'arc_list' key?
            # should the arc_list case be wrapped in an AND to be consistent?

            # TODO Testing this
            # params_dict['arclist_list'] = parse_dict.get('arclist_list', None)

            if arc_list is not None:
                params_dict['arclist_list'] = parse_dict.get('arc_list', None)
            else:
                params_dict['arclist_list'] = parse_dict.get('arclist_list', None)

            params_dict['constraint_list_list'] = parse_dict.get('constraint_list_list', None)

            params_dict['node_binding'] = parse_dict.get('node_binding', None)
            params_dict['edge_binding'] = parse_dict.get('edge_binding', None)
            params_dict['path_binding'] = parse_dict.get('path_binding', None)
            params_dict['solution_binding'] = parse_dict.get('solution_binding', None)

            params_dict['arc_traverse_type'] = parse_dict.get('arc_traverse_type', None)
            params_dict['arc_direction_type'] = parse_dict.get('arc_direction_type', None)

            arc = MetaQLBuilder.build_arc(**params_dict)

            return arc

        if metaql_class in ['AndArcList', 'OrArcList']:

            arc_list_type = None

            if metaql_class == 'AndArcList':
                arc_list_type = AND_ARC_LIST_TYPE

            if metaql_class == 'OrArcList':
                arc_list_type = OR_ARC_LIST_TYPE

            # are we using the key 'arc_list' ?
            arc_list_list = metaql_dict.get('arc_list', None)

            arclist_list = metaql_dict.get('arclist_list', None)

            # print(f"arc_list_list: {arc_list_list}")

            # print(f"arclist_list: {arclist_list}")

            # TODO in this path we seems to be using the entire arc list or arc list list as it is
            # and not getting and recursively parsing the individual elements
            # which means some things like NodeBinding are used from the source json and not from parsing
            # which may cause validation errors as the components didn't go through validation.

            arc_list = MetaQLBuilder.build_arc_list(
                arc_list_type=arc_list_type,
                arc_list_list=arc_list_list,
                arclist_list=arclist_list
            )

            return arc_list

        if metaql_class in ['AndConstraintList','OrConstraintList']:

            constraint_list_type = None

            if metaql_class == 'AndConstraintList':
                constraint_list_type = AND_CONSTRAINT_LIST_TYPE

            if metaql_class == 'OrConstraintList':
                constraint_list_type = OR_CONSTRAINT_LIST_TYPE

            constraint_list = metaql_dict.get('constraint_list', None)

            constraint_list = MetaQLBuilder.build_constraint_list(
                constraint_list_type=constraint_list_type,
                constraint_list=constraint_list
            )
            return constraint_list

        if metaql_class in [
            'NodeConstraint',
            'EdgeConstraint',
            'HyperNodeConstraint',
            'HyperEdgeConstraint'
        ]:

            params_dict = {}

            class_constraint_type = None

            if metaql_class == 'NodeConstraint':
                class_constraint_type = NODE_CLASS_CONSTRAINT_TYPE

            if metaql_class == 'EdgeConstraint':
                class_constraint_type = EDGE_CLASS_CONSTRAINT_TYPE

            if metaql_class == 'HyperNodeConstraint':
                class_constraint_type = HYPER_NODE_CLASS_CONSTRAINT_TYPE

            if metaql_class == 'HyperEdgeConstraint':
                class_constraint_type = HYPER_EDGE_CLASS_CONSTRAINT_TYPE

            params_dict['class_constraint_type'] = class_constraint_type
            params_dict['class_uri'] = parse_dict.get('class_uri', None)
            params_dict['include_subclasses'] = parse_dict.get('include_subclasses', None)

            class_constraint = MetaQLBuilder.build_class_constraint(**params_dict)

            return class_constraint

        if metaql_class in [
            'VectorConstraintVectorValue',
            'VectorConstraintTextValue'
        ]:

            params_dict = {}

            vector_constraint_type = None

            if metaql_class == 'VectorConstraintVectorValue':
                vector_constraint_type = VECTOR_CONSTRAINT_TYPE_VECTOR

            if metaql_class == 'VectorConstraintTextValue':
                vector_constraint_type = VECTOR_CONSTRAINT_TYPE_TEXT

            params_dict['vector_constraint_type'] = vector_constraint_type
            params_dict['vector_comparator_type'] = parse_dict.get('vector_comparator_type', None)
            params_dict['class_uri'] = parse_dict.get('class_uri', None)
            params_dict['vector_name'] = parse_dict.get('vector_name', None)
            params_dict['text_constraint_value'] = parse_dict.get('text_constraint_value', None)
            params_dict['vector_constraint_value'] = parse_dict.get('vector_constraint_value', None)

            vector_constraint = MetaQLBuilder.build_vector_constraint(**params_dict)

            return vector_constraint

        if metaql_class in [
            'EXISTS_PROPERTY_CONSTRAINT_TYPE',
            'NOT_EXISTS_PROPERTY_CONSTRAINT_TYPE',
            'STRING_PROPERTY_CONSTRAINT_TYPE',
            'BOOLEAN_PROPERTY_CONSTRAINT_TYPE',
            'INTEGER_PROPERTY_CONSTRAINT_TYPE',
            'FLOAT_PROPERTY_CONSTRAINT_TYPE',
            'URI_PROPERTY_CONSTRAINT_TYPE',
            'DATETIME_PROPERTY_CONSTRAINT_TYPE',
            'LONG_PROPERTY_CONSTRAINT_TYPE',
            'DOUBLE_PROPERTY_CONSTRAINT_TYPE',
            'GEOLOCATION_PROPERTY_CONSTRAINT_TYPE',
            'TRUTH_PROPERTY_CONSTRAINT_TYPE',
            'OTHER_PROPERTY_CONSTRAINT_TYPE'
        ]:

            params_dict = {}

            params_dict['property_constraint_type'] = parse_dict.get('property_constraint_type', None)
            params_dict['target'] = parse_dict.get('target', None)
            params_dict['property_uri'] = parse_dict.get('property_uri', None)
            params_dict['comparator'] = parse_dict.get('comparator', None)
            params_dict['include_subproperties'] = parse_dict.get('include_subproperties', None)

            params_dict['string_value'] = parse_dict.get('string_value', None)
            params_dict['boolean_value'] = parse_dict.get('boolean_value', None)
            params_dict['float_value'] = parse_dict.get('float_value', None)
            params_dict['integer_value'] = parse_dict.get('integer_value', None)
            params_dict['long_value'] = parse_dict.get('long_value', None)
            params_dict['double_value'] = parse_dict.get('double_value', None)
            params_dict['other_value'] = parse_dict.get('other_value', None)
            params_dict['geolocation_value'] = parse_dict.get('geolocation_value', None)
            params_dict['truth_value'] = parse_dict.get('truth_value', None)
            params_dict['datetime_value'] = parse_dict.get('datetime_value', None)

            property_constraint = MetaQLBuilder.build_property_constraint(**params_dict)

            return property_constraint

        if metaql_class == 'MetaQLResponse':

            params_dict = {}

            params_dict['result_status'] = parse_dict.get('result_status', None)
            params_dict['result_list'] = parse_dict.get('result_list', None)

            metaql_response = MetaQLBuilder.build_response(**params_dict)

            return metaql_response

        if metaql_class == 'MetaQLStatus':

            params_dict = {}

            params_dict['status_type'] = parse_dict.get('status_type', None)
            params_dict['status_code'] = parse_dict.get('status_code', None)
            params_dict['status_message'] = parse_dict.get('status_message', None)

            metaql_status = MetaQLBuilder.build_status(**params_dict)

            return metaql_status

        if metaql_class == 'MetaQLResultList':

            params_dict = {}

            params_dict['offset'] = parse_dict.get('offset', None)
            params_dict['limit'] = parse_dict.get('limit', None)
            params_dict['result_count'] = parse_dict.get('result_count', None)
            params_dict['total_result_count'] = parse_dict.get('total_result_count', None)
            params_dict['binding_list'] = parse_dict.get('binding_list', None)
            params_dict['result_list'] = parse_dict.get('result_list', None)

            graph_object_json_list = metaql_dict['result_object_list']

            result_object_list = []

            if graph_object_json_list:
                for go_dict in graph_object_json_list:
                    go = GraphObject.from_json_map(go_dict)
                    result_object_list.append(go)

            params_dict['result_object_list'] = result_object_list

            result_list = MetaQLBuilder.build_result_list(**params_dict)

            return result_list

        if metaql_class == 'MetaQLResultElement':

            params_dict = {}

            params_dict['score'] = parse_dict.get('score', None)

            graph_object_json = metaql_dict['graph_object']

            graph_object = GraphObject.from_json_map(graph_object_json)

            params_dict['graph_object'] = graph_object

            result_element = MetaQLBuilder.build_result_element(**params_dict)

            return result_element

        return None
