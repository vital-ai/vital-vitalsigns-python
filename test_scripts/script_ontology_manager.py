import logging
import os
import sys
from datetime import datetime
import importlib_metadata
from ai_haley_kg_domain.model.KGChatBotMessage import KGChatBotMessage
from rdflib import Namespace, OWL, RDF, RDFS, BNode, XSD
from vital_ai_domain.model.Edge_hasVitalOntNode import Edge_hasVitalOntNode
from vital_ai_domain.model.VitalOntEdge import VitalOntEdge
from vital_ai_domain.model.VitalOntNode import VitalOntNode
from vital_ai_vitalsigns.model.GraphObject import GraphObject
from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
from vital_ai_vitalsigns.model.properties.DateTimeProperty import DateTimeProperty
from vital_ai_vitalsigns.model.properties.DoubleProperty import DoubleProperty
from vital_ai_vitalsigns.model.properties.GeoLocationProperty import GeoLocationProperty
from vital_ai_vitalsigns.model.properties.IntegerProperty import IntegerProperty
from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
from vital_ai_vitalsigns.model.properties.TruthProperty import TruthProperty
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
import inspect

matplotlib.use('TkAgg')


def get_class_hierarchy(clz, top_level_class):

    hierarchy = []
    current_class = clz

    while current_class is not top_level_class:
        hierarchy.append(current_class)
        current_class = current_class.__bases__[0]
        if current_class is object:
            break
    hierarchy.append(top_level_class)

    return hierarchy


def get_property_class_from_rdf_type(rdf_type_iri):

    if rdf_type_iri == str(XSD.boolean):
        return BooleanProperty
    elif rdf_type_iri == str(XSD.string):
        return StringProperty
    elif rdf_type_iri == str(XSD.integer):
        return IntegerProperty
    elif rdf_type_iri == str(XSD.int):
        return IntegerProperty
    elif rdf_type_iri == str(XSD.long):
        return IntegerProperty
    elif rdf_type_iri == str(XSD.double):
        return DoubleProperty
    elif rdf_type_iri == str(XSD.float):
        return DoubleProperty
    elif rdf_type_iri == str(XSD.dateTime):
        return DateTimeProperty
    elif rdf_type_iri == "http://vital.ai/ontology/vital-core#geoLocation":
        return GeoLocationProperty
    elif rdf_type_iri == "http://vital.ai/ontology/vital-core#truth":
        return TruthProperty
    elif rdf_type_iri == str(XSD.anyURI):
        return StringProperty
    else:
        return None


def main():

    print('Test Ontology Manager')

    before_time = datetime.now()

    # logging.basicConfig(level=logging.INFO)

    print(f"Initializing ontologies... ")

    vs = VitalSigns()

    after_time = datetime.now()

    delta = after_time - before_time

    delta_seconds = delta.total_seconds()

    print(f"Initialized Ontologies in: {delta_seconds} seconds.")

    registry = vs.get_registry()

    ont_manager = vs.get_ontology_manager()

    domain_graph = ont_manager.get_domain_graph()

    domain_triple_count = len(domain_graph)

    print(f"Domain Triple Count: {domain_triple_count}.")

    ont_list = ont_manager.get_ontology_iri_list()

    for ont_iri in ont_list:

        ont = ont_manager.get_vitalsigns_ontology(ont_iri)

        package_name = ont.get_package_name()

        ont_graph = ont.get_ontology_graph()

        print(f"Ontology IRI: {ont_iri} Package: {package_name} Triple Count: {len(ont_graph)}.")

    kg_prefix = "haley-ai-kg"
    kg_ont_iri = 'http://vital.ai/ontology/haley-ai-kg#'
    kg_ont = ont_manager.get_vitalsigns_ontology(kg_ont_iri)
    kg_ont_graph = kg_ont.get_ontology_graph()

    kg_ont_path = kg_ont.get_ontology_path()

    kg_package_name = ont.get_package_name()

    print(f"KG Ont Package: {package_name} Path: {kg_ont_path}.")

    # kg_ns = Namespace(kg_ont_iri)
    # kg_ont_graph.bind(kg_prefix, kg_ns)

    # query to get class URIs from the ontology
    # and then get the corresponding class object in python
    query = f"""
        PREFIX {kg_prefix}: <{kg_ont_iri}>
        SELECT DISTINCT ?type
        WHERE {{
            ?type a owl:Class .
            FILTER (strstarts(str(?type), str(haley-ai-kg:)))
        }}
    """

    results = kg_ont_graph.query(query)

    for row in results:
        class_uri = str(row['type'])
        graph_object_cls = registry.vitalsigns_classes[class_uri]
        module_name = graph_object_cls.__module__
        module = sys.modules[module_name]
        package_name = module.__package__
        #  package_name will be top_package_name + "model"
        # ai_haley_kg_domain.model from ai_haley_kg_domain
        top_package_name = package_name.split('.')[0]
        # print(f"Class URI: {class_uri} in Class Package: {package_name} from {kg_package_name}")

    # TODO test queries for getting properties, data types

    # test queries for getting annotations
    # annotations on edges can be used to determine edge source/destinations

    # source_annotation = "http://vital.ai/ontology/vital-core#hasEdgeSrcDomain"
    # destination_annotation = "http://vital.ai/ontology/vital-core#hasEdgeDestDomain"

    ann_query = """
    PREFIX vital-core: <http://vital.ai/ontology/vital-core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>

    SELECT ?class ?annotation ?value
    WHERE {
    ?class rdfs:subClassOf* vital-core:VITAL_Edge .
    
    {
        ?class vital-core:hasEdgeSrcDomain ?value .
        BIND(vital-core:hasEdgeSrcDomain AS ?annotation)
    }
    UNION
    {
        ?class vital-core:hasEdgeDestDomain ?value .
        BIND(vital-core:hasEdgeDestDomain AS ?annotation)
    }
    }
    """

    results = domain_graph.query(ann_query)

    for row in results:
        class_uri = str(row['class'])
        annotation_uri = str(row['annotation'])
        value_uri = str(row['value'])

        # print(f"{class_uri}, {annotation_uri}, {value_uri}")

    for s, p, o in kg_ont_graph.triples((None, None, None)):
        # print(f"{s}, {p}, {o}")
        pass

    # print(f"Triple Count: {len(kg_ont_graph)}")

    def extract_classes(expression, graph):
        classes = set()
        if isinstance(expression, BNode):
            for s, p, o in graph.triples((expression, None, None)):
                if p == OWL.unionOf or p == OWL.intersectionOf:
                    for item in graph.items(o):
                        classes.update(extract_classes(item, graph))
                else:
                    classes.update(extract_classes(o, graph))
        else:
            if (expression, RDF.type, OWL.Class) in graph or (expression, RDF.type, RDFS.Class) in graph:
                classes.add(expression)
        return classes

    data_property_query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?classExpression ?dataProperty ?dataType
    WHERE {
        ?dataProperty rdf:type owl:DatatypeProperty .
        ?dataProperty rdfs:domain ?classExpression .
        ?dataProperty rdfs:range ?dataType .
    }
    """

    results = domain_graph.query(data_property_query)

    data_prop_results_dict = {}

    for row in results:
        class_expression = row['classExpression']
        data_property_uri = str(row['dataProperty'])
        data_type_uri = str(row['dataType'])

        # Extract all classes from the class expression
        domain_classes = list(extract_classes(class_expression, domain_graph))

        # Add to results dictionary
        if data_property_uri not in data_prop_results_dict:
            data_prop_results_dict[data_property_uri] = {"domain": set(), "dataType": data_type_uri}

        data_prop_results_dict[data_property_uri]["domain"].update(domain_classes)

    # Convert sets to lists and prepare the final results
    final_results = []
    for prop_uri, domain_and_type in data_prop_results_dict.items():
        final_results.append((
            list(domain_and_type["domain"]),
            prop_uri,
            domain_and_type["dataType"]
        ))

    # Print the final results
    for domain_classes, data_property_uri, data_type_uri in final_results:
        # print(f"Data Domain Classes: {domain_classes}, Property: {data_property_uri}, Data Type: {data_type_uri}")
        pass

    object_property_query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?classExpression ?objectProperty ?rangeExpression
    WHERE {
        ?objectProperty rdf:type owl:ObjectProperty .
        ?objectProperty rdfs:domain ?classExpression .
        ?objectProperty rdfs:range ?rangeExpression .
    }
    """

    results = domain_graph.query(object_property_query)

    ont_prop_results_dict = {}

    for row in results:
        class_expression = row['classExpression']
        object_property_uri = str(row['objectProperty'])
        range_expression = row['rangeExpression']

        # Extract all classes from the class expression and range expression
        domain_classes = list(extract_classes(class_expression, domain_graph))
        range_classes = list(extract_classes(range_expression, domain_graph))

        # Add to results dictionary
        if object_property_uri not in ont_prop_results_dict:
            ont_prop_results_dict[object_property_uri] = {"domain": set(), "range": set()}

        ont_prop_results_dict[object_property_uri]["domain"].update(domain_classes)
        ont_prop_results_dict[object_property_uri]["range"].update(range_classes)

    # Convert sets to lists and prepare the final results
    final_results = []

    for prop_uri, domains_and_ranges in ont_prop_results_dict.items():
        final_results.append((
            list(domains_and_ranges["domain"]),
            prop_uri,
            list(domains_and_ranges["range"])
        ))

    # Print the final results
    for domain_classes, object_property_uri, range_classes in final_results:
        # print(f"Ont Domain Classes: {domain_classes}, Property: {object_property_uri}, Range Classes: {range_classes}")
        pass

    # "?class rdf:type owl:Class ."
    # "?class rdfs:subClassOf* vital:VITAL_Node ."

    class_query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX vital: <http://vital.ai/ontology/vital-core#>
    PREFIX haley-ai-kg: <http://vital.ai/ontology/haley-ai-kg#>

    SELECT ?class ?label ?parent
    WHERE {
        ?class rdfs:subClassOf haley-ai-kg:KGMedia .

        OPTIONAL { ?class rdfs:label ?label }
        OPTIONAL { ?class rdfs:subClassOf ?parent }
    }
    """

    # Execute the query
    results = domain_graph.query(class_query)

    # Dictionaries to hold nodes and edges
    nodes = {}
    edges = []

    kgmedia_node = VitalOntNode()
    kgmedia_node.URI = URIGenerator.generate_uri()
    kgmedia_node.name = "KGMedia"
    nodes["http://vital.ai/ontology/haley-ai-kg#KGMedia"] = kgmedia_node

    # Process the results
    for row in results:
        class_uri = str(row['class'])
        label = str(row['label']) if row['label'] else class_uri.split('#')[-1]
        parent_uri = str(row['parent']) if row['parent'] else None

        # print(f"Class URI: {class_uri}, Label: {label}, Parent URI: {parent_uri}")

        # Create or get the node
        if class_uri not in nodes:
            node = VitalOntNode()
            node.URI = URIGenerator.generate_uri()
            node.name = label
            nodes[class_uri] = node

        # Create or get the parent node
        if parent_uri:
            if parent_uri not in nodes:
                parent_node = VitalOntNode()
                parent_node.URI = URIGenerator.generate_uri()
                parent_node.name = parent_uri.split('#')[-1]
                nodes[parent_uri] = parent_node

            # Create the edge
            edge = Edge_hasVitalOntNode()
            edge.URI = URIGenerator.generate_uri()
            edge.edgeSource = nodes[parent_uri].URI
            edge.edgeDestination = nodes[class_uri].URI
            edge.name = "parentOf"
            edges.append(edge)

    # Create a NetworkX graph
    G = nx.DiGraph()

    # Add nodes to the graph
    for node in nodes.values():
        # print(f"Adding node: {node.URI} with label: {node.name}")

        G.add_node(str(node.URI), label=node.name)

    # Add edges to the graph
    for edge in edges:
        # print(f"Adding edge from {edge.edgeSource} to {edge.edgeDestination} with label: {edge.name}")

        G.add_edge(str(edge.edgeSource), str(edge.edgeDestination), label=edge.name)

    # Draw the graph
    pos = nx.spring_layout(G)
    labels = nx.get_node_attributes(G, 'label')
    edge_labels = nx.get_edge_attributes(G, 'label')

    nx.draw(G, pos, with_labels=True, labels=labels, node_size=3000, node_color='lightblue', font_size=10,
            font_weight='bold')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    # display graph
    # plt.show()

    domain_property_map = {}

    range_property_map = {}

    for prop_uri, domain_and_type in data_prop_results_dict.items():

        class_list = list(domain_and_type["domain"])

        data_type = domain_and_type["dataType"]

        prop_class = get_property_class_from_rdf_type(data_type)

        if prop_class is None:
            print(f"No property class found for {data_type}")
            exit(0)

        property_range_map = {
            "property_uri": prop_uri,
            "property_type": "DataProperty",
            "data_type": data_type,
            "prop_class": prop_class
        }

        range_property_map[prop_uri] = property_range_map

        # print(f"Data Prop: {class_list} {prop_uri} {data_type}")

        for clz in class_list:
            clz = str(clz)
            if clz in domain_property_map.keys():
                class_map = domain_property_map[clz]
                class_prop_set = class_map["prop_set"]
            else:
                class_map = {}
                domain_property_map[clz] = class_map
                class_prop_set = set()
                class_map["prop_set"] = class_prop_set
            class_prop_set.add(prop_uri)

    for prop_uri, domains_and_ranges in ont_prop_results_dict.items():

        class_list = list(domains_and_ranges["domain"])

        range_list = list(domains_and_ranges["range"])

        property_range_map = {
            "property_uri": prop_uri,
            "property_type": "ObjectProperty",
            "range_class_list": range_list,
            "prop_class": URIProperty
        }

        range_property_map[prop_uri] = property_range_map

        # print(f"Ont Prop: {class_list} {prop_uri} {range_list}")

        for clz in class_list:
            clz = str(clz)
            if clz in domain_property_map.keys():
                class_map = domain_property_map[clz]
                class_prop_set = class_map["prop_set"]
            else:
                class_map = {}
                domain_property_map[clz] = class_map
                class_prop_set = set()
                class_map["prop_set"] = class_prop_set

            class_prop_set.add(prop_uri)

    clazz = KGChatBotMessage

    class_list = get_class_hierarchy(clazz, GraphObject)

    prop_set = set()

    for c in class_list:
        if c.get_class_uri():
            clazz_uri = str(c.get_class_uri())
            # print(f"Class URI: {clazz_uri}")

            # print(domain_property_map.keys())
            # print(len(domain_property_map.keys()))

            class_map = domain_property_map.get(clazz_uri)
            if class_map:
                class_prop_set = class_map["prop_set"]
                prop_set.update(class_prop_set)

    for p in prop_set:
        prop_map = range_property_map[p]
        prop_class = prop_map["prop_class"]
        # print(f"Property: {p} : {prop_class.__name__}")

    bot_message = KGChatBotMessage()

    bot_message.name = "Bot"

    bot_message.objectCreationTime = datetime.now()

    print(bot_message.objectCreationTime)

    print(bot_message.to_json())


if __name__ == "__main__":
    main()
