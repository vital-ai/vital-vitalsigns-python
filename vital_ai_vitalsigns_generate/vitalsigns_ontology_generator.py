import re
import yaml
from owlready2 import default_world, get_ontology, ThingClass, Or, ObjectProperty, DataProperty, AnnotationProperty, \
    ObjectPropertyClass
from rdflib import URIRef, RDF, RDFS, XSD, OWL
from vital_ai_vitalsigns_generate.generate.class_generator import VitalSignsClassGenerator
from vital_ai_vitalsigns_generate.generate.property_trait_generator import VitalSignsPropertyTraitGenerator


class VitalSignsOntologyGenerator:

    # Constants
    has_multi_values_ann_iri = "http://vital.ai/ontology/vital-core#hasMultipleValues"
    default_package_iri = "http://vital.ai/ontology/vital-core#hasDefaultPackage"

    def __init__(self):
        pass


    def is_model_class(self, class_name):

        model_class_list = [
            "GraphObject",
            "VITAL_Edge",
            "VITAL_GraphContainerObject",
            "VITAL_HyperEdge",
            "VITAL_HyperNode",
            "VITAL_Node"
        ]

        if class_name in model_class_list:
            return True

        return False

    def get_model_class_package(self):
        model_class_package = "vital_ai_vitalsigns.model"

        return model_class_package

    def generate_property_code(self, ont_model, ont_prop):

        has_multi_values_ann = ont_model.search(iri=VitalSignsOntologyGenerator.has_multi_values_ann_iri)[0]

        multi_values = False

        if hasattr(ont_prop, has_multi_values_ann.name):  # has_multi_values_ann.name):
            annotation_value = getattr(ont_prop, has_multi_values_ann.name)  # has_multi_values_ann.name)
            if annotation_value:
                multi_values = annotation_value[0]

        class_name = "Property_" + ont_prop.name
        namespace = ont_prop.namespace.base_iri
        local_name = ont_prop.name
        multiple_values = multi_values

        property_trait_code = VitalSignsPropertyTraitGenerator.generate_property_trait_string(class_name, namespace, local_name, multiple_values)

        return property_trait_code

    def generate_class_code(self, ont_list, ont_model, ont_class):

        # get hasDefaultPackage
        package_name = "ai_haley_kg_domain.model"
        parent_package_name = "ai_haley_kg_domain.model"

        parent_base_iri, parent_class_name = self.get_parent_class(ont_class)

        parent_ont = self.get_ontology(ont_list, parent_base_iri)

        default_parent_package = self.get_default_package(parent_ont)

        # TODO lookup for vital-core and vital packages
        # vital-core is at the top of the hierarchy so it doesn't have a parent
        # vital_domain_package = "vital_ai_domain"

        # TODO adjusting package name, +.model + .properties

        if len(default_parent_package) == 0:
            default_parent_package = ['vital_ai_vitalsigns_core']

        parent_package_name = default_parent_package[0]

        parent_package_name = parent_package_name.replace('.', '_')

        parent_class_import = f"{parent_package_name}.model.{parent_class_name}"

        if self.is_model_class(parent_class_name):
            model_package = self.get_model_class_package()
            parent_class_import = f"{model_package}.{parent_class_name}"

        class_name = ont_class.name
        class_uri = ont_class.iri

        domain_props = self.get_domain(ont_list, ont_model, class_uri)

        property_list = []

        for d in domain_props:

            print(f"Domain: {d.iri}")
            print(f"Domain Range: {d.range_iri}")
            print(f"Domain Prop Type: {type(d)}")

            range_list = self.get_range(ont_model, d)

            prop_class = 'StringProperty'

            if isinstance(d, ObjectPropertyClass):
                print(f"Domain Object Property: {d} Range List: {range_list}")

                # URI case
                prop_class = 'StringProperty'
            else:
                print(f"Domain Data Property: {d} Range List: {range_list}")
                prop_class = 'StringProperty'
                if len(range_list) == 1:
                    prop_class = self.range_to_data_property(range_list[0])

            p_map = {'uri': d.iri, 'prop_class': prop_class}
            property_list.append(p_map)

        class_code = VitalSignsClassGenerator.generate_class_string(
            parent_class_import,
            parent_class_name,
            class_name,
            class_uri,
            property_list)

        return class_code

    def generate_class_interface_code(self, ont_list, ont_model, ont_class):

        package_name = "ai_haley_kg_domain.model"

        parent_package_name = "ai_haley_kg_domain.model"

        parent_base_iri, parent_class_name = self.get_parent_class(ont_class)

        parent_ont = self.get_ontology(ont_list, parent_base_iri)

        default_parent_package = self.get_default_package(parent_ont)

        # TODO have lookup for vital-core and vital-domain
        if len(default_parent_package) == 0:
            default_parent_package = ['vital_ai_vitalsigns_core']

        # TODO adjusting package name, +.model + .properties

        parent_package_name = default_parent_package[0]

        parent_package_name = parent_package_name.replace('.', '_')

        parent_class_import = f"{parent_package_name}.model.{parent_class_name}"

        if self.is_model_class(parent_class_name):
            model_package = self.get_model_class_package()
            parent_class_import = f"{model_package}.{parent_class_name}"

        class_name = ont_class.name
        class_uri = ont_class.iri

        domain_props = self.get_domain(ont_list, ont_model, class_uri)

        property_interface_list = []

        for d in domain_props:

            print(f"Domain: {d.iri}")
            print(f"Domain Range: {d.range_iri}")
            print(f"Domain Prop Type: {type(d)}")

            range_list = self.get_range(ont_model, d)

            data_type = 'str'

            if isinstance(d, ObjectPropertyClass):

                print(f"Domain Object Property: {d} Range List: {range_list}")

                # URI case
                data_type = 'str'
            else:
                print(f"Domain Data Property: {d} Range List: {range_list}")
                data_type = 'str'
                if len(range_list) == 1:
                    data_type = self.xsd_to_data_type(range_list[0])

            name = d.name
            short_name = self.get_short_name(name)

            p_map = {'short_prop_name': short_name, 'datatype': data_type}
            property_interface_list.append(p_map)

        # properties = [
        #    {'short_prop_name': 'kGAgentAvatarImageSourceURL', 'datatype': 'str'},
        # ]

        class_interface_code = VitalSignsClassGenerator.generate_class_interface_string(
            parent_class_import,
            parent_class_name,
            class_name,
            property_interface_list)

        return class_interface_code

    def get_ontology(self, ont_list, ont_iri):

        for ontology in ont_list:
            print(f"Ontology Base URI: {ontology.base_iri}")
            print(f"Parent Base URI: {ont_iri}")
            if ontology.base_iri == ont_iri:
                return ontology

        return None

    def get_parent_class(self, ont_class):

        parent_classes = ont_class.is_a

        for parent in parent_classes:
            parent_base_iri = parent.namespace.base_iri
            print(f"Parent class of {ont_class.name}: {parent_base_iri} {parent.name}")
            parent_class_name = parent.name
            parent_iri = parent.iri

        return parent_base_iri, parent_class_name

    def get_short_name(self, local_name) -> str:
        """Transforms the local name into a short name by removing prefixes and lowercasing the initial letter."""
        name = local_name
        if name.startswith("has"):
            name = name[3:]
        elif name.startswith("is"):
            name = name[2:]

        # Lowercase the first letter and return
        return name[0].lower() + name[1:] if name else name

    def get_domain(self, ont_list, ont_model, class_uri):

        print(f"Class URI: {class_uri}")

        domain_props = []

        for ontology in ont_list:

            for prop in ontology.properties():

                prop_domain = prop.domain

                for domain in prop_domain:

                    if not domain:
                        continue

                    # print(f"Domain: {domain}")

                    if isinstance(domain, Or):
                        for clz in domain.Classes:
                            domain_iri = clz.iri
                            # print(f"Handling OR domain class: {domain_iri}")
                            if domain_iri == class_uri:
                                domain_props.append(prop)
                    else:
                        domain_iri = domain.iri
                        # print(f"Handling domain class: {domain_iri}")
                        if domain_iri == class_uri:
                            domain_props.append(prop)

        print(f"Domain Prop Count: {len(domain_props)}")

        return domain_props

    def get_range(self, ont_model, ont_prop):

        range_list = []

        prop_range = ont_prop.range_iri

        print(f"prop_range: {prop_range}")

        for rng in prop_range:

            print(f"Range Type: {type(rng)} : {rng}")

            if isinstance(rng, str):

                if rng.startswith("_"):
                    print(f"Encountered a blank node: {rng}")

                    graph = default_world.as_rdflib_graph()

                    # value like: _:117
                    match = re.search(r'_:([0-9]+)', rng)

                    blank_iri = match.group(1)

                    for s, p, o in graph.triples((None, None, None)):
                        # print(f"Triple: {s} {p} {o}")
                        if str(s) == blank_iri:
                            print(f"Triple: {s} {p} {o}")
                            for union_s, union_p, union_o in graph.triples((s, OWL.unionOf, None)):
                                for item in graph.items(union_o):
                                    print(f"Handling union range class: {item}")
                                    range_list.append(item)

                else:

                    if rng in XSD:
                        print(f"Handling Range XSD DataType: {rng}")
                        range_list.append(rng)
                    else:
                        graph = default_world.as_rdflib_graph()

                        if self.is_custom_datatype(graph, rng):
                            print(f"Handling Range Custom DataType: {rng}")
                            range_list.append(rng)
                        else:
                            entity = ont_model.search_one(iri=rng)

                            if isinstance(entity, ThingClass):
                                print(f"Handling Range Class: {entity.iri}")
                                range_list.append(entity.iri)
                            else:
                                print(f"Range String Type Unknown: {rng}")
            else:
                print(f"Range Type Unknown: {rng}")

        return range_list

    def get_default_package(self, ont_model):

        annotation_values = {}

        annotations = ont_model.world.sparql(
            f"""
                SELECT ?value WHERE {{
                    <{ont_model.base_iri}> <{VitalSignsOntologyGenerator.default_package_iri}> ?value .
                }}
            """
        )

        annotation_values[VitalSignsOntologyGenerator.default_package_iri] = [value[0] for value in annotations]

        print(f"Default Package: {annotation_values[VitalSignsOntologyGenerator.default_package_iri]}")

        default_package = annotation_values[VitalSignsOntologyGenerator.default_package_iri]

        return default_package

    def is_custom_datatype(self, graph, iri) -> bool:
        iri_ref = URIRef(iri)
        for s, p, o in graph.triples((iri_ref, RDF.type, RDFS.Datatype)):
            return True
        return False

    def range_to_data_property(self, range_iri):

        if range_iri == str(XSD.boolean):
            return "BooleanProperty"
        elif range_iri == str(XSD.string):
            return "StringProperty"
        elif range_iri == str(XSD.integer):
            return "IntegerProperty"
        elif range_iri == str(XSD.int):
            return "IntegerProperty"
        elif range_iri == str(XSD.long):
            return "IntegerProperty"
        elif range_iri == str(XSD.double):
            return "DoubleProperty"
        elif range_iri == str(XSD.float):
            return "DoubleProperty"
        elif range_iri == str(XSD.dateTime):
            return "DateTimeProperty"
        elif range_iri == "http://vital.ai/ontology/vital-core#geoLocation":
            return "GeoLocationProperty"
        elif range_iri == "http://vital.ai/ontology/vital-core#truth":
            return "TruthProperty"
        elif range_iri == str(XSD.anyURI):
            return "StringProperty"
        else:
            return None

    def xsd_to_data_type(self, xsd_iri):
        if xsd_iri == str(XSD.boolean):
            return "bool"
        elif xsd_iri == str(XSD.string):
            return "str"
        elif xsd_iri == str(XSD.integer):
            return "int"
        elif xsd_iri == str(XSD.int):
            return "int"
        elif xsd_iri == str(XSD.long):
            return "int"
        elif xsd_iri == str(XSD.double):
            return "float"
        elif xsd_iri == str(XSD.float):
            return "float"
        elif xsd_iri == str(XSD.dateTime):
            return "datetime"
        elif xsd_iri == "http://vital.ai/ontology/vital-core#geoLocation":
            return "str"
        elif xsd_iri == "http://vital.ai/ontology/vital-core#truth":
            return "str"
        elif xsd_iri == str(XSD.anyURI):
            return "str"
        else:
            return "Unsupported data type"

    def load_ontologies(self, generate_ontology_iri: str, iri_to_file_map: dict, domain_list_file_path: str):

        generate_ontology = None

        ontology_list = []

        for k in iri_to_file_map.keys():
            print(k)

        for v in iri_to_file_map.values():
            print(v)

        generate_ontology_file_path = iri_to_file_map[generate_ontology_iri]

        with open(domain_list_file_path, 'r') as file:
            data = yaml.safe_load(file)

        for item in data['domains']:
            domain = item['domain']
            ontology = item['ontology']
            print(f"Domain: {domain}, Ontology: {ontology}")

            if generate_ontology_file_path.endswith(ontology):

                print(f"Loading {ontology}...")

                print(f"Ontology file {ontology}: {generate_ontology_file_path}")

                original_get_ontology = default_world.get_ontology

                def custom_resolver(iri, iri_to_file_map):
                    """Custom resolver function for mapping IRIs to local files."""
                    return iri_to_file_map.get(iri, iri)

                def get_ontology_with_resolver(iri):
                    resolved_iri = custom_resolver(iri, iri_to_file_map)
                    print(f"Resolving IRI: {iri} to {resolved_iri}")
                    return original_get_ontology(resolved_iri)

                default_world.get_ontology = get_ontology_with_resolver

                ontology_model = get_ontology(generate_ontology_file_path).load()

                for imported_ontology in ontology_model.imported_ontologies:
                    print(f"Imported ontology: {imported_ontology}")

                def load_all_imports(ontology):
                    imported_ontologies = list(ontology.imported_ontologies)
                    for imported_ontology in ontology.imported_ontologies:
                        imported_ontologies.extend(load_all_imports(imported_ontology))
                    return imported_ontologies

                # Load all transitive imports
                all_imported_ontologies = load_all_imports(ontology_model)

                ontology_list = [ontology_model]

                # Ensure that all imported ontologies are loaded
                for ont in all_imported_ontologies:
                    print(f"Loading: {ont}")
                    ont_loaded = ont.load()
                    ontology_list.append(ont_loaded)

                generate_ontology = ontology_model

                break

        return generate_ontology, ontology_list

    def print_property_info(self, ont_model, ont_prop):

        has_multi_values_ann = ont_model.search(iri=VitalSignsOntologyGenerator.has_multi_values_ann_iri)[0]

        multi_values = False

        if hasattr(ont_prop, has_multi_values_ann.name):  # has_multi_values_ann.name):
            annotation_value = getattr(ont_prop, has_multi_values_ann.name)  # has_multi_values_ann.name)
            if annotation_value:
                multi_values = annotation_value[0]

        print(f"Ont Prop {ont_prop.name} multi values: {multi_values}")

        if ObjectProperty in ont_prop.is_a:
            print(f"Ont Prop {ont_prop.name} Object Property")
        elif DataProperty in ont_prop.is_a:
            print(f"Ont Prop {ont_prop.name} Data Property")
        elif AnnotationProperty in ont_prop.is_a:
            print(f"Ont Prop {ont_prop.name} Annotation Property")
        else:
            print(f"Ont Prop {ont_prop.name} Unknown Property Type")

        prop_domain = ont_prop.domain

        prop_range = ont_prop.range_iri

        # Ont Prop hasIntegerValue Range: ['http://www.w3.org/2001/XMLSchema#int']

        print(f"Ont Prop {ont_prop.name} Domain: {prop_domain}")

        for domain in prop_domain:
            print(f"Domain: {domain}")
            if isinstance(domain, Or):
                for cls in domain.Classes:
                    print(f"Handling OR domain class: {cls.iri}")

        print(f"Ont Prop {ont_prop.name} Range: {prop_range}")

        for rng in prop_range:

            print(f"Range Type: {type(rng)} : {rng}")

            if isinstance(rng, str):

                if rng.startswith("_"):
                    print(f"Encountered a blank node: {rng}")

                    graph = default_world.as_rdflib_graph()

                    # value like: _:117
                    match = re.search(r'_:([0-9]+)', rng)

                    blank_iri = match.group(1)

                    for s, p, o in graph.triples((None, None, None)):
                        # print(f"Triple: {s} {p} {o}")
                        if str(s) == blank_iri:
                            print(f"Triple: {s} {p} {o}")
                            for union_s, union_p, union_o in graph.triples((s, OWL.unionOf, None)):
                                for item in graph.items(union_o):
                                    print(f"Handling union range class: {item}")

                else:

                    if rng in XSD:
                        print(f"Handling Range XSD DataType: {rng}")
                    else:

                        graph = default_world.as_rdflib_graph()

                        if self.is_custom_datatype(graph, rng):
                            print(f"Handling Range Custom DataType: {rng}")
                        else:
                            entity = ont_model.search_one(iri=rng)

                            if isinstance(entity, ThingClass):
                                print(f"Handling Range Class: {entity.iri}")
                            else:
                                print(f"Range String Type Unknown: {rng}")
            else:
                print(f"Range Type Unknown: {rng}")

