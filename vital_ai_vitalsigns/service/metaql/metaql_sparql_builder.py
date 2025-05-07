from typing import List

from typing_extensions import Dict

from vital_ai_vitalsigns.metaql.arc.metaql_arc import ArcRoot, Arc, ARC_TRAVERSE_TYPE_EDGE, ARC_TRAVERSE_TYPE_PROPERTY, \
    ARC_DIRECTION_TYPE_FORWARD, ARC_DIRECTION_TYPE_REVERSE
from vital_ai_vitalsigns.metaql.arc_list.metaql_arc_list import OrArcList, AndArcList, MetaQLArcList
from vital_ai_vitalsigns.metaql.constraint_list.metaql_constraint_list import MetaQLConstraintList
from vital_ai_vitalsigns.metaql.metaql_query import MetaQLQuery, GraphQuery
from vital_ai_vitalsigns.service.metaql.metaql_constraint_list_impl import AndConstraintListImpl, OrConstraintListImpl, \
    MetaQLConstraintListImpl
from vital_ai_vitalsigns.service.metaql.metaql_sparql_impl import MetaQLSparqlImpl
from vital_ai_vitalsigns.vitalsigns import VitalSigns


class MetaQLSparqlBuilder:

    # switch to instance variables
    root_arc_id = 0
    current_arc_id: int = 1

    global_term_id: int = 1

    binding_map: Dict[int,str] = {}

    # idea to implement the OR-case optimization
    # generate list of terms within the deepest OR
    # for terms that are the same in all OR cases, take out of the OR
    # and move into an AND (the unique ones).

    # in the case of the frame query, the terms for the KG Entities would be in separate
    # lists of unique terms until the top level OR would merge them by extracting the
    # same ones and leaving the unique constraints on the name/description
    # in the OR to become the contents of the UNION.

    # terms would be the same if they involve the same bound name,
    # otherwise they would be tied to a unique identifier

    # terms should be localized within the arc, but consider to what degree
    # terms may involve the parent bound name

    # by having source entity and destination entity as the bound names
    # we can separate them, but when we try to label these both as entity
    # then differentiating them must involve the parent bound name (source and destination slot)

    # it seems we should keep node binding hooked to the name used
    # in the multiple places (source entity, destination entity)
    # and not use ?entity as a binding name
    # however we could add a new case for "solution binding"
    # to allow differentiating which of the OR cases matched
    # so:
    # .node_bind(NodeBind(name="source_entity"))
    # and
    # .solution_bind(SolutionBind(name="entity"))
    # which can add an extra:
    # BIND(?sourceSlotEntity as ?entity)
    # to link the node binding to the extra name

    # once edge binding names are used then those should be shared
    # and not unique per or-group
    # KGSlot uses sub-classes so will need to include those
    # if constraining on the type

    def build_sparql(self, metaql_query: MetaQLQuery, *,
                     base_uri: str|None = None, namespace: str|None = None, account_id: str|None = None, is_global: bool = False) -> MetaQLSparqlImpl | None:

        # print(metaql_query)

        metaql_class = metaql_query.get('metaql_class', None)

        # print(f"MetaQL Class: {metaql_class}")

        if metaql_class == 'SelectQuery':
            # TODO
            pass

        if metaql_class == 'GraphQuery':

            sparql_impl = MetaQLSparqlImpl()

            graph_query: GraphQuery = metaql_query

            sparql_impl_out = self.build_graph_query(
                graph_query=graph_query,
                sparql_impl=sparql_impl)

            limit = sparql_impl_out.get_limit()
            offset = sparql_impl_out.get_offset()
            resolve_objects = sparql_impl_out.get_resolve_objects()

            graph_uri_list = sparql_impl_out.get_graph_uri_list()

            graph_id_list = sparql_impl_out.get_graph_id_list()


            # graph_uri = graph_uri_list[0]

            graph_id = graph_id_list[0]

            # TODO add account_id

            if is_global:
                graph_uri = f"{base_uri}/{namespace}/GLOBAL/{graph_id}"
            else:
                graph_uri = f"{base_uri}/{namespace}/{graph_id}"


            # print("Binding List:")
            # for binding in sparql_impl_out.get_binding_list():
            #    print(f"Binding: {binding}")

            bind_list = " ".join([f"?{bind}" for bind in sparql_impl_out.get_binding_list()])

            # print("Sparql Terms:")
            # for term in sparql_impl_out.get_arc_constraint_list():
            #    print(term)

            term_list = "\n".join(sparql_impl_out.get_arc_constraint_list())

            # print("Bind Constraint List:")
            # for bind in sparql_impl_out.get_bind_constraint_list():
            #    print(f"Bind Constraint: {bind}")

            bind_constraint_list = "\n".join(sparql_impl_out.get_bind_constraint_list())

            namespace_list_string = """
PREFIX vital-core: <http://vital.ai/ontology/vital-core#>
PREFIX vital: <http://vital.ai/ontology/vital#>
PREFIX vital-aimp: <http://vital.ai/ontology/vital-aimp#>
PREFIX haley: <http://vital.ai/ontology/haley>
PREFIX haley-ai-question: <http://vital.ai/ontology/haley-ai-question#>
PREFIX haley-ai-kg: <http://vital.ai/ontology/haley-ai-kg#>"""

            sparql_string = f"""
{namespace_list_string}
            
SELECT distinct {bind_list} WHERE {{

    GRAPH <{graph_uri}> {{

{term_list}

{bind_constraint_list}
    }}
}}
LIMIT {limit}
OFFSET {offset}          
"""

            # print(f"Sparql String:\n{sparql_string}")

            return sparql_impl_out

        return None

    def build_graph_query(self, *,
                          graph_query: GraphQuery,
                          sparql_impl: MetaQLSparqlImpl) -> MetaQLSparqlImpl:

        limit = graph_query.get('limit', None)
        offset = graph_query.get('offset', None)
        resolve_objects = graph_query.get('resolve_objects', None)
        graph_uri_list = graph_query.get('graph_uri_list', None)
        graph_id_list = graph_query.get('graph_id_list', None)

        sparql_impl.set_limit(limit)
        sparql_impl.set_offset(offset)
        sparql_impl.set_resolve_objects(resolve_objects)
        sparql_impl.set_graph_uri_list(graph_uri_list)
        sparql_impl.set_graph_id_list(graph_id_list)


        arc: Arc | ArcRoot | None = graph_query.get('arc', None)

        metaql_class = arc.get('metaql_class', None)

        arc_root_id = self.root_arc_id

        sparql_impl_out: MetaQLSparqlImpl | None = None

        if metaql_class == 'ArcRoot':
            sparql_impl_out = self.build_arc_root(
                arc_root=arc,
                sparql_impl=sparql_impl,
                arc_id=arc_root_id
            )

        return sparql_impl_out

    def build_arc_root(self, *,
                       arc_root: ArcRoot,
                       sparql_impl: MetaQLSparqlImpl,
                       arc_id: int) -> MetaQLSparqlImpl:

        # print("building arc root...")

        depth = 0
        or_context: bool = False
        # print(f"Depth: {depth}, OrContext: {or_context}")
        # print(f"Root Arc Id: {arc_id}")
        # print(arc_root)

        leaf = True

        node_binding = arc_root.get('node_binding', None)
        edge_binding = arc_root.get('edge_binding', None)
        path_binding = arc_root.get('path_binding', None)
        solution_binding = arc_root.get('solution_binding', None)

        node_binding_name = None
        edge_binding_name = None
        path_binding_name = None
        solution_binding_name = None

        if node_binding:
            binding = node_binding.get('binding', None)
            # print(f"Node Binding: {binding}")
            node_binding_name = binding
            sparql_impl.add_binding(node_binding_name)
            sparql_impl.set_root_binding(node_binding_name)

            self.binding_map[arc_id] = binding

        if edge_binding:
            binding = edge_binding.get('binding', None)
            # print(f"Edge Binding: {binding}")
            edge_binding_name = binding
            sparql_impl.add_binding(edge_binding_name)

        if path_binding:
            binding = path_binding.get('binding', None)
            # print(f"Path Binding: {binding}")
            path_binding_name = binding
            sparql_impl.add_binding(path_binding_name)

        if solution_binding:
            binding = solution_binding.get('binding', None)
            # print(f"Solution Binding: {binding}")
            solution_binding_name = binding
            sparql_impl.add_binding(solution_binding_name)

        terms = []

        arc: Arc | None = arc_root.get('arc', None)

        if arc:

            self.current_arc_id += 1
            child_arc_id = self.current_arc_id

            # print(f"child_arc_id: {child_arc_id}")

            sparql_impl_out = self.build_arc(
                arc=arc,
                sparql_impl=sparql_impl,
                depth=depth,
                or_context=or_context,
                parent_arc_id=arc_id,
                arc_id=child_arc_id)
            leaf = False

        arclist_list = arc_root.get('arclist_list', None)

        for arclist in arclist_list:

            # print(f"arclist: {arclist}")

            metaql_class = arclist.get('metaql_class', None)

            if metaql_class == 'OrArcList':
                sparql_impl_out = self.build_or_arc_list(
                    or_arc_list=arclist,
                    sparql_impl=sparql_impl,
                    depth=depth,
                    or_context=or_context,
                    parent_arc_id=arc_id,

                )

            if metaql_class == 'AndArcList':
                sparql_impl_out = self.build_and_arc_list(
                    and_arc_list=arclist,
                    sparql_impl=sparql_impl,
                    depth=depth,
                    or_context=or_context,
                    parent_arc_id=arc_id,

                )

            leaf = False

        node_binding_name = self.binding_map[arc_id]

        constraint_list_list: List[MetaQLConstraintList] = arc_root.get('constraint_list_list', None)

        constraint_terms = self.build_constraint_term_list(
            node_binding_name=node_binding_name,
            constraint_list_list=constraint_list_list)

        for ct in constraint_terms:
            terms.append(ct)

        for term in terms:
            sparql_impl.add_arc_constraint(term)
            # print(f"Term: {term}")

        # print(f"ArcRoot Leaf: {leaf}")

        return sparql_impl

    def build_arc(self, *,
                  arc: Arc,
                  sparql_impl: MetaQLSparqlImpl,
                  depth: int,
                  or_context: bool = False,
                  parent_arc_id: int,
                  arc_id: int) -> MetaQLSparqlImpl:

        # print("building arc...")
        # print(f"Depth: {depth}, OrContext: {or_context}")
        # print(f"Parent Arc Id: {parent_arc_id}, Arc Id: {arc_id}")
        # print(arc)
        # print(f"Binding Map: {self.binding_map}")

        node_binding = arc.get('node_binding', None)
        edge_binding = arc.get('edge_binding', None)
        path_binding = arc.get('path_binding', None)
        solution_binding = arc.get('solution_binding', None)

        node_binding_name = None
        edge_binding_name = None
        path_binding_name = None
        solution_binding_name = None

        if node_binding:
            binding = node_binding.get('binding', None)
            # print(f"Node Binding: {binding}")
            node_binding_name = binding
            sparql_impl.add_binding(node_binding_name)
            self.binding_map[arc_id] = binding

        if edge_binding:
            binding = edge_binding.get('binding', None)
            # print(f"Edge Binding: {binding}")
            edge_binding_name = binding
            sparql_impl.add_binding(edge_binding_name)

        if path_binding:
            binding = path_binding.get('binding', None)
            # print(f"Path Binding: {binding}")
            path_binding_name = binding
            sparql_impl.add_binding(path_binding_name)

        if solution_binding:
            binding = solution_binding.get('binding', None)
            # print(f"Solution Binding: {binding}")
            solution_binding_name = binding
            sparql_impl.add_binding(solution_binding_name)

        arc_traverse_type = arc.get('arc_traverse_type', None)

        arc_direction_type = arc.get('arc_direction_type', None)

        terms: List[str] = []

        # node bindings
        parent_arc_binding = self.binding_map[parent_arc_id]

        # print(f"binding map: {self.binding_map}")

        arc_binding = self.binding_map[arc_id]

        if arc_traverse_type == ARC_TRAVERSE_TYPE_EDGE:
            if arc_direction_type == ARC_DIRECTION_TYPE_FORWARD:

                # term = f"{parent_arc_binding} --edge--> {arc_binding}"

                if edge_binding_name:
                    edge_binding_variable = edge_binding_name
                else:
                    edge_binding_variable = f"{arc_binding}_{arc_id}_edge"

                term1 = f"?{edge_binding_variable} vital-core:hasEdgeSource ?{parent_arc_binding} ."
                term2 = f"?{edge_binding_variable} vital-core:hasEdgeDestination ?{arc_binding} ."

                terms.extend([term1, term2])

            if arc_direction_type == ARC_DIRECTION_TYPE_REVERSE:
                # term = f"{parent_arc_binding} <--edge-- {arc_binding}"

                if edge_binding_name:
                    edge_binding_variable = edge_binding_name
                else:
                    edge_binding_variable = f"{arc_binding}_{arc_id}_edge"

                term1 = f"?{edge_binding_variable} vital-core:hasEdgeDestination ?{parent_arc_binding} ."
                term2 = f"?{edge_binding_variable} vital-core:hasEdgeSource ?{arc_binding} ."

                terms.extend([term1, term2])

        if arc_traverse_type == ARC_TRAVERSE_TYPE_PROPERTY:

            property_path_list_list = arc.get('property_path_list_list', None)

            property_path = property_path_list_list[0][0]

            property_uri = property_path.get('property_uri', None)

            if arc_direction_type == ARC_DIRECTION_TYPE_FORWARD:
                # term = f"{parent_arc_binding} property--> {arc_binding}"

                term1 = f"?{parent_arc_binding} <{property_uri}> ?{arc_binding} ."

                if path_binding_name:
                    path_binding_term = f"BIND(?{parent_arc_binding} as ?{path_binding_name})"
                    sparql_impl.add_bind_constraint(path_binding_term)

                terms.extend([term1])

            if arc_direction_type == ARC_DIRECTION_TYPE_REVERSE:
                # term = f"{parent_arc_binding} <--property {arc_binding}"

                term1 = f"?{arc_binding} <{property_uri}> ?{parent_arc_binding} ."

                if path_binding_name:
                    path_binding_term = f"BIND(?{arc_binding} as ?{path_binding_name})"
                    sparql_impl.add_bind_constraint(path_binding_term)

                terms.extend([term1])

        leaf = True

        sub_arc: Arc | None = arc.get('arc', None)

        arclist_list: MetaQLArcList | None = arc.get('arclist_list', None)

        if sub_arc:

            self.current_arc_id += 1
            child_arc_id = self.current_arc_id

            sparql_impl_out = self.build_arc(
                arc=sub_arc,
                sparql_impl=sparql_impl,
                depth=depth + 1,
                or_context=or_context,
                parent_arc_id=arc_id,
                arc_id=child_arc_id
            )

            leaf = False

        for arclist in arclist_list:

            metaql_class = arclist.get('metaql_class', None)

            if metaql_class == 'OrArcList':

                sparql_impl_out = self.build_or_arc_list(
                    or_arc_list=arclist,
                    sparql_impl=sparql_impl,
                    depth=depth + 1,
                    or_context=or_context,
                    parent_arc_id=arc_id,

                )

            if metaql_class == 'AndArcList':

                sparql_impl_out = self.build_and_arc_list(
                    and_arc_list=arclist,
                    sparql_impl=sparql_impl,
                    depth=depth + 1,
                    or_context=or_context,
                    parent_arc_id=arc_id,

                )

            leaf = False

        # print(f"Arc Leaf: {leaf}")

        node_binding_name = self.binding_map[arc_id]

        constraint_list_list: List[MetaQLConstraintList] = arc.get('constraint_list_list', None)

        constraint_terms = self.build_constraint_term_list(
            node_binding_name=node_binding_name,
            constraint_list_list=constraint_list_list
        )

        for ct in constraint_terms:
            terms.append(ct)

        for term in terms:
            # print(f"Term: {term}")
            sparql_impl.add_arc_constraint(term)

        if solution_binding:
            solution_binding_name = solution_binding.get('binding', None)
            solution_term = f"BIND(?{arc_binding} as ?{solution_binding_name})"
            sparql_impl.add_bind_constraint(solution_term)

        return sparql_impl

    def build_constraint_term_list(self, *,
                                   node_binding_name: str,
                                   constraint_list_list: List[MetaQLConstraintList]
                                   ) -> List[str]:

        constraint_list_impl_list = []

        terms = []

        for metaql_constraint_list in constraint_list_list:

            metaql_class = metaql_constraint_list.get('metaql_class', None)

            constraint_list = metaql_constraint_list.get('constraint_list', None)

            constraint_list_impl: MetaQLConstraintListImpl = None

            if metaql_class == 'AndConstraintList':
                constraint_list_impl = AndConstraintListImpl()

            if metaql_class == 'OrConstraintList':
                constraint_list_impl = OrConstraintListImpl()

            if constraint_list_impl:

                for constraint in constraint_list:

                    constraint_class = constraint.get('metaql_class', None)

                    if constraint_class == "NodeConstraint":

                        include_subclasses = constraint.get('include_subclasses', False)

                        if include_subclasses:

                            vs = VitalSigns()

                            class_uri = constraint.get('class_uri', None)

                            subclass_list =  vs.get_ontology_manager().get_subclass_uri_list(class_uri)

                            subclass_list_name = f"{node_binding_name}_subclass_list"
                            subclass_list_string = "\n".join([f"<{subclass}>" for subclass in subclass_list])

                            subclass_value_term = f"""
VALUES ?{subclass_list_name } {{
{subclass_list_string}
}}
"""

                            term1 = subclass_value_term
                            term2 = f"?{node_binding_name} a ?{node_binding_name}_type ."
                            term3 = f"FILTER(?{node_binding_name}_type IN (?{subclass_list_name}))"

                            constraint_list_impl.add_constraint(term1 + "\n" + term2 + "\n" + term3)

                        else:
                            class_uri = constraint.get('class_uri', None)
                            term = f"?{node_binding_name} a <{class_uri}> ."

                            constraint_list_impl.add_constraint(term)

                    if constraint_class == "URIPropertyConstraint":

                        property_uri = constraint.get('property_uri', None)
                        uri_value = constraint.get('uri_value', None)

                        term = f"?{node_binding_name} <{property_uri}> <{uri_value}> ."
                        constraint_list_impl.add_constraint(term)

                    if constraint_class == 'StringPropertyConstraint':
                        property_uri = constraint.get('property_uri')
                        string_value = constraint.get('string_value')

                        term_id = self.global_term_id
                        self.global_term_id += 1

                        term = f"""
                        ?{node_binding_name} <{property_uri}> ?term_{term_id} .
                        ?term_{term_id} bif:contains "{string_value}" .
                        """
                        constraint_list_impl.add_constraint(term)

                constraint_list_impl_list.append(constraint_list_impl)

        # for the moment just add as terms
        # constraint lists currently are flat and don't contain sub-lists
        for constraint_list in constraint_list_impl_list:

            if isinstance(constraint_list, AndConstraintListImpl):
                for constraint in constraint_list.get_constraints():
                    terms.append(constraint)

            if isinstance(constraint_list, OrConstraintListImpl):
                curly_list = [f"{{\n{term}\n}}\n" for term in constraint_list.get_constraints()]
                union_string = "\nUNION\n".join(curly_list)
                terms.append(union_string)

        return terms

    def build_or_arc_list(self, *,
                          or_arc_list: OrArcList,
                          sparql_impl: MetaQLSparqlImpl,
                          depth: int,
                          or_context: bool = False,
                          parent_arc_id: int) -> MetaQLSparqlImpl:

        # print("building or-arc list...")
        # print(f"Depth: {depth}, OrContext: {or_context}")
        # print(f"Parent Arc Id: {parent_arc_id}")

        # print(or_arc_list)

        leaf = True

        arc_list: List[Arc] | None = or_arc_list.get("arc_list", None)

        for arc in arc_list:

            self.current_arc_id += 1
            child_arc_id = self.current_arc_id

            sparql_impl_out = self.build_arc(
                arc=arc,
                sparql_impl=sparql_impl,
                depth=depth + 1,
                or_context=True,
                parent_arc_id=parent_arc_id,
                arc_id=child_arc_id
            )

            leaf = False

        arclist_list: List[MetaQLArcList] | None = or_arc_list.get("arclist_list", None)

        impl_list = []

        for arclist in arclist_list:

            metaql_class = arclist.get('metaql_class', None)

            or_sparql_impl = MetaQLSparqlImpl()

            if metaql_class == 'OrArcList':

                sparql_impl_out = self.build_or_arc_list(
                    or_arc_list=arclist,
                    sparql_impl=sparql_impl,
                    depth=depth + 1,
                    or_context=True,
                    parent_arc_id=parent_arc_id,
                )
                # TODO should this be added?
                #  sparql_impl_out
                # impl_list.append(sparql_impl_out)

            if metaql_class == 'AndArcList':

                sparql_impl_out = self.build_and_arc_list(
                    and_arc_list=arclist,
                    sparql_impl=or_sparql_impl,
                    depth=depth + 1,
                    or_context=True,
                    parent_arc_id=parent_arc_id,

                )

                impl_list.append(sparql_impl_out)

            leaf = False

        term_set = set()
        and_term_list = []

        bind_set = set()
        and_bind_list = []

        for impl in impl_list:

            for constraint in impl.get_arc_constraint_list():
                term_set.add(constraint)

            for bind_constraint in impl.get_bind_constraint_list():
                bind_set.add(bind_constraint)

        # for term in term_set:
        #    print(f"Unique Term: {term}")

        # for bind in bind_set:
        #    print(f"Unique Bind Term: {bind}")

        for term in term_set:

            all_or = True

            for impl in impl_list:

                if not term in impl.get_arc_constraint_list():
                    all_or = False

            if all_or:
                for impl in impl_list:
                    impl.get_arc_constraint_list().remove(term)
                and_term_list.append(term)

        # print("All List:")

        # for term in and_term_list:
        #    print(f"All Term: {term}")

        for bind in bind_set:

            all_or = True

            for impl in impl_list:

                if not bind in impl.get_bind_constraint_list():
                    all_or = False

            if all_or:
                for impl in impl_list:
                    impl.get_bind_constraint_list().remove(bind)
                and_bind_list.append(bind)

        # print("All Bind List:")

        # for bind in and_bind_list:
        #    print(f"All Bind : {bind}")

        # put the top level AND ones in the list
        for term in and_term_list:
            sparql_impl.add_arc_constraint(term)

        for bind in and_bind_list:
            sparql_impl.add_bind_constraint(bind)

        # print("Remaining OR Terms:")

        count = 0

        for impl in impl_list:

            count += 1

            # print(f"Set: {count}")

            # for term in impl.get_arc_constraint_list():
            #    print(f"(Set {count}): Term: {term}")

        count = 0

        for impl in impl_list:

            count += 1

            # print(f"Bind Set: {count}")

            # for bind in impl.get_bind_constraint_list():
            #    print(f"(Set {count}): Bind: {bind}")

        or_term_string: str | None = None

        or_impl_list = []

        for impl in impl_list:
            curly_list = [f"{{\n{term}\n}}\n" for term in impl.get_arc_constraint_list()]
            curly_string = "\n".join(curly_list)

            curly_bind_list = [f"\n{term}\n" for term in impl.get_bind_constraint_list()]

            curly_string += "".join(curly_bind_list)

            curly_group = f"{{\n{curly_string}\n}}\n"

            or_impl_list.append(curly_group)

        if len(or_impl_list) == 0:
            pass
        elif len(or_impl_list) == 1:
            or_term_string = or_impl_list[0]
        elif len(or_impl_list) >  1:
            or_union_string = "\nUNION\n".join(or_impl_list)
            or_term_string = or_union_string

        if or_term_string:
            sparql_impl.add_arc_constraint(or_term_string)

        for impl in impl_list:
            for binding in impl.get_binding_list():
                sparql_impl.add_binding(binding)

        # print(f"OrArcList Leaf: {leaf}")

        return sparql_impl

    def build_and_arc_list(self, *,
                           and_arc_list: AndArcList,
                           sparql_impl: MetaQLSparqlImpl,
                           depth: int,
                           or_context: bool = False,
                           parent_arc_id: int) -> MetaQLSparqlImpl:

        leaf = True

        # print("building and-arc list...")
        # print(f"Depth: {depth}, OrContext: {or_context}")
        # print(f"Parent Arc Id: {parent_arc_id}")
        # print(and_arc_list)

        arc_list: List[Arc] | None = and_arc_list.get("arc_list", None)

        for arc in arc_list:

            self.current_arc_id += 1
            child_arc_id = self.current_arc_id

            sparql_impl_out = self.build_arc(
                arc=arc,
                sparql_impl=sparql_impl,
                depth=depth + 1,
                or_context=or_context,
                parent_arc_id=parent_arc_id,
                arc_id=child_arc_id
            )
            leaf = False

        arclist_list: List[MetaQLArcList] | None = and_arc_list.get("arclist_list", None)

        for arclist in arclist_list:

            metaql_class = arclist.get('metaql_class', None)

            if metaql_class == 'OrArcList':

                sparql_impl_out = self.build_or_arc_list(
                    or_arc_list=arclist,
                    sparql_impl=sparql_impl,
                    depth=depth + 1,
                    or_context=or_context,
                    parent_arc_id=parent_arc_id,
                )

            if metaql_class == 'AndArcList':

                sparql_impl_out = self.build_and_arc_list(
                    and_arc_list=arclist,
                    sparql_impl=sparql_impl,
                    depth=depth + 1,
                    or_context=or_context,
                    parent_arc_id=parent_arc_id,
                )

            leaf = False

        # print(f"AndArcList Leaf: {leaf}")

        return sparql_impl
