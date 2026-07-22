import re
import yaml
from owlready2 import default_world, get_ontology, ThingClass, Or, ObjectProperty, DataProperty, AnnotationProperty, \
    ObjectPropertyClass, AnnotationPropertyClass
from rdflib import URIRef, RDF, RDFS, XSD, OWL
from vital_ai_vitalsigns_generate.generate.class_generator import VitalSignsClassGenerator
from vital_ai_vitalsigns_generate.generate.property_trait_generator import VitalSignsPropertyTraitGenerator


class VitalSignsOntologyGenerator:

    # Constants
    has_multi_values_ann_iri = "http://vital.ai/ontology/vital-core#hasMultipleValues"
    default_package_iri = "http://vital.ai/ontology/vital-core#hasDefaultPackage"

    vital_core_ont_iri = "http://vital.ai/ontology/vital-core"
    vital_ont_iri = "http://vital.ai/ontology/vital"

    # Non-graph-object classes, skipped for class file generation and
    # property-domain matching. Ported from the hardcoded set in the Groovy
    # generator (nonGraphObjectClasses, PythonDomainGenerator.groovy:92) —
    # keep in sync with vitalsigns-source.
    non_graph_object_class_uris = {
        "http://vital.ai/ontology/vital-core#RestrictionAnnotationValue"
    }

    # Version pattern required by owl:versionInfo validation.
    version_info_pattern = re.compile(r"^\d+\.\d+\.\d+$")

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

    def get_parent_import(self, ont_list, ont_class):
        """Resolve the parent class name and its import package.

        Groovy special cases:
        - root model class -> vital_ai_vitalsigns.model
        - parent from vital-core -> vital_ai_vitalsigns_core.model
        - parent from vital -> vital_ai_domain.model
        - otherwise -> parent ontology hasDefaultPackage ('.'->'_') + .model
        """

        parent_base_iri, parent_class_name = self.get_parent_class(ont_class)

        if self.is_model_class(parent_class_name):
            model_package = self.get_model_class_package()
            return parent_class_name, f"{model_package}.{parent_class_name}"

        parent_ont_iri = parent_base_iri.rstrip('#/')

        if parent_ont_iri == VitalSignsOntologyGenerator.vital_core_ont_iri:
            return parent_class_name, f"vital_ai_vitalsigns_core.model.{parent_class_name}"

        if parent_ont_iri == VitalSignsOntologyGenerator.vital_ont_iri:
            return parent_class_name, f"vital_ai_domain.model.{parent_class_name}"

        parent_ont = self.get_ontology(ont_list, parent_base_iri)

        default_parent_package = self.get_default_package(parent_ont) if parent_ont is not None else []

        if len(default_parent_package) == 0:
            raise ValueError(
                f"Cannot resolve parent package for class {ont_class.iri}: "
                f"parent ontology {parent_base_iri} has no "
                f"{VitalSignsOntologyGenerator.default_package_iri} annotation")

        parent_package_name = default_parent_package[0].replace('.', '_')

        return parent_class_name, f"{parent_package_name}.model.{parent_class_name}"

    def get_property_class(self, ont_model, ont_prop):
        """Map a property to its VitalSigns property class name (Groovy mapping)."""

        range_list = self.get_range(ont_model, ont_prop)

        if isinstance(ont_prop, ObjectPropertyClass):
            print(f"Domain Object Property: {ont_prop} Range List: {range_list}")
            # object property -> URI
            return 'URIProperty'

        print(f"Domain Data Property: {ont_prop} Range List: {range_list}")

        if len(range_list) == 1:
            return self.range_to_data_property(range_list[0])

        # empty or union range -> OtherProperty (Groovy behavior)
        return 'OtherProperty'

    def generate_class_code(self, ont_list, ont_model, ont_class):

        parent_class_name, parent_class_import = self.get_parent_import(ont_list, ont_class)

        class_name = ont_class.name
        class_uri = ont_class.iri

        domain_props = self.get_domain(ont_list, ont_model, class_uri)

        property_list = []

        for d in domain_props:

            print(f"Domain: {d.iri}")
            print(f"Domain Range: {d.range_iri}")
            print(f"Domain Prop Type: {type(d)}")

            prop_class = self.get_property_class(ont_model, d)

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

        parent_class_name, parent_class_import = self.get_parent_import(ont_list, ont_class)

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
        seen_prop_iris = set()

        for ontology in ont_list:

            for prop in ontology.properties():

                # annotation properties are never graph object properties
                if isinstance(prop, AnnotationPropertyClass):
                    continue

                if prop.iri in seen_prop_iris:
                    continue

                prop_domain = prop.domain

                for domain in prop_domain:

                    if not domain:
                        continue

                    # print(f"Domain: {domain}")

                    if isinstance(domain, Or):
                        for clz in domain.Classes:
                            domain_iri = clz.iri
                            # print(f"Handling OR domain class: {domain_iri}")
                            if domain_iri == class_uri and prop.iri not in seen_prop_iris:
                                domain_props.append(prop)
                                seen_prop_iris.add(prop.iri)
                    else:
                        domain_iri = domain.iri
                        # print(f"Handling domain class: {domain_iri}")
                        if domain_iri == class_uri and prop.iri not in seen_prop_iris:
                            domain_props.append(prop)
                            seen_prop_iris.add(prop.iri)

        # Sort into the order produced by the Groovy generator
        # (OntologyProcessor.listOntologyPropertiesSorted, effective behavior):
        # ascending count of transitive super-properties belonging to the
        # generated ontology, tie-broken by full property URI (case-sensitive).
        domain_props.sort(key=lambda p: self.property_sort_key(ont_model, p))

        print(f"Domain Prop Count: {len(domain_props)}")

        return domain_props

    def property_sort_key(self, ont_model, ont_prop):
        """Groovy-parity property sort key: (same-ontology ancestor property
        count, full URI). See parity spec §2 — replicates the *effective*
        comparator behavior including its dead foreign-ontology branch."""

        ont_prefix = ont_model.base_iri

        count = 0
        seen = set()
        stack = list(getattr(ont_prop, 'is_a', []))

        while stack:
            parent = stack.pop()
            parent_iri = getattr(parent, 'iri', None)
            if parent_iri is None or parent_iri in seen or parent_iri == ont_prop.iri:
                continue
            seen.add(parent_iri)
            if parent_iri.startswith(ont_prefix):
                count += 1
            stack.extend(getattr(parent, 'is_a', []))

        return count, ont_prop.iri

    def class_sort_key(self, ont_model, ont_class):
        """Groovy-parity class sort key: ascending count of same-ontology
        ancestor classes (parents first); ties keep iteration order (use with
        a stable sort)."""

        ont_prefix = ont_model.base_iri

        count = 0
        for ancestor in ont_class.ancestors():
            if ancestor is ont_class:
                continue
            ancestor_iri = getattr(ancestor, 'iri', None)
            if ancestor_iri and ancestor_iri.startswith(ont_prefix):
                count += 1

        return count

    def should_generate_class(self, ont_class):
        """Filtering (parity spec §4): skip root model classes (they live in
        vital_ai_vitalsigns.model) and non-graph-object classes."""

        if self.is_model_class(ont_class.name):
            return False

        if ont_class.iri in VitalSignsOntologyGenerator.non_graph_object_class_uris:
            return False

        return True

    def should_generate_trait(self, ont_model, ont_prop):
        """Filtering (parity spec §4/§6): skip annotation properties, skip
        properties defined in other ontologies (DSLD domain extensions get
        their trait from the defining ontology's package), and skip properties
        whose domains are all non-graph-object classes."""

        if isinstance(ont_prop, AnnotationPropertyClass):
            return False

        # trait lives in the defining ontology's package only
        if ont_prop.namespace.base_iri.rstrip('#/') != ont_model.base_iri.rstrip('#/'):
            return False

        domain_class_iris = []
        for domain in ont_prop.domain:
            if not domain:
                continue
            if isinstance(domain, Or):
                domain_class_iris.extend(clz.iri for clz in domain.Classes)
            else:
                domain_class_iris.append(domain.iri)

        if domain_class_iris and all(
                iri in VitalSignsOntologyGenerator.non_graph_object_class_uris
                for iri in domain_class_iris):
            return False

        return True

    def get_root_class_names(self):
        return {
            "GraphObject",
            "VITAL_Edge",
            "VITAL_GraphContainerObject",
            "VITAL_HyperEdge",
            "VITAL_HyperNode",
            "VITAL_Node"
        }

    def get_class_annotation_entities(self, ont_class, ann_name):
        """Collect annotation values for ann_name on the class or, if absent,
        the nearest declaration on an ancestor class."""

        for cls in [ont_class] + list(ont_class.ancestors()):
            try:
                values = list(getattr(cls, ann_name, None) or [])
            except Exception:
                values = []
            if values:
                return values
        return []

    def validate_ontology(self, ont_model, ont_list):
        """Validation ported from the Groovy generator (parity spec §7).
        Raises ValueError listing all violations; callers must run this before
        writing any output file (all-or-nothing)."""

        errors = []

        root_class_names = self.get_root_class_names()

        # owl:versionInfo present and matching the version pattern
        version_values = [
            str(row[0]) for row in ont_model.world.sparql(
                f"""
                    SELECT ?value WHERE {{
                        <{ont_model.base_iri}> <http://www.w3.org/2002/07/owl#versionInfo> ?value .
                    }}
                """
            )
        ]

        if len(version_values) == 0:
            errors.append(f"Ontology {ont_model.base_iri} has no owl:versionInfo annotation")
        elif not any(VitalSignsOntologyGenerator.version_info_pattern.match(v) for v in version_values):
            errors.append(
                f"Ontology {ont_model.base_iri} owl:versionInfo {version_values} "
                f"does not match the required version pattern")

        for ont_class in ont_model.classes():

            if not self.should_generate_class(ont_class):
                continue

            # single direct parent class
            direct_parents = [p for p in ont_class.is_a if isinstance(p, ThingClass)]
            if len(direct_parents) > 1:
                errors.append(
                    f"Class {ont_class.iri} has more than one direct parent: "
                    f"{[p.iri for p in direct_parents]}")

            # must descend from a root graph object class
            ancestor_names = {a.name for a in ont_class.ancestors()}
            if not (ancestor_names & root_class_names):
                errors.append(
                    f"Class {ont_class.iri} does not descend from a root graph object class")

            # edge / hyperedge domain annotations
            if "VITAL_Edge" in ancestor_names and ont_class.name != "VITAL_Edge":
                errors.extend(self.validate_edge_domains(
                    ont_class, "hasEdgeSrcDomain", "hasEdgeDestDomain"))

            if "VITAL_HyperEdge" in ancestor_names and ont_class.name != "VITAL_HyperEdge":
                # hyperedge src/dest may be any graph object class, not just
                # VITAL_Node (Groovy PythonDomainGenerator.groovy:1243-1253
                # only resolves the class, no VITAL_Node check — unlike edges
                # at :1113)
                errors.extend(self.validate_edge_domains(
                    ont_class, "hasHyperEdgeSrcDomain", "hasHyperEdgeDestDomain",
                    require_node=False))

        for ont_prop in ont_model.properties():

            if isinstance(ont_prop, AnnotationPropertyClass):
                continue

            # single parent property
            parent_props = [
                p for p in ont_prop.is_a
                if getattr(p, 'iri', None)
                and not p.iri.startswith("http://www.w3.org/")
                and p.iri != ont_prop.iri
            ]
            if len(parent_props) > 1:
                errors.append(
                    f"Property {ont_prop.iri} has more than one parent property: "
                    f"{[p.iri for p in parent_props]}")

            # a property from a parent ontology may only have its domain
            # extended to classes of the ontology being generated
            if ont_prop.namespace.base_iri.rstrip('#/') != ont_model.base_iri.rstrip('#/'):
                for domain in ont_prop.domain:
                    if not domain:
                        continue
                    domain_classes = domain.Classes if isinstance(domain, Or) else [domain]
                    for clz in domain_classes:
                        clz_iri = getattr(clz, 'iri', None)
                        if clz_iri is None:
                            continue
                        clz_ont_iri = clz_iri.rsplit('#', 1)[0]
                        prop_ont_iri = ont_prop.namespace.base_iri.rstrip('#/')
                        ont_iri = ont_model.base_iri.rstrip('#/')
                        if clz_ont_iri != ont_iri and clz_ont_iri != prop_ont_iri:
                            errors.append(
                                f"Property {ont_prop.iri} from parent ontology extends its "
                                f"domain to class {clz_iri} which is not a class of the "
                                f"ontology being generated ({ont_iri})")

        if errors:
            error_text = "\n".join(f"- {e}" for e in errors)
            raise ValueError(
                f"Ontology validation failed for {ont_model.base_iri}:\n{error_text}")

    def validate_edge_domains(self, ont_class, src_ann_name, dest_ann_name,
                              require_node=True):
        """Edge/hyperedge domain annotations, when present (directly or
        inherited), must each resolve to a class; for edges (require_node)
        the class must additionally be a VITAL_Node subclass.

        NOTE: the parity spec (§7) requires >=1 src/dest annotation, but the
        committed Groovy-generated vital-core baseline contains edge base
        classes (VITAL_PeerEdge, VITAL_TaxonomyEdge) without any, so absence
        is accepted with a warning to avoid failing valid baselines."""

        errors = []

        for ann_name in (src_ann_name, dest_ann_name):

            values = self.get_class_annotation_entities(ont_class, ann_name)

            if len(values) == 0:
                print(f"WARNING: Edge class {ont_class.iri} has no {ann_name} annotation")
                continue

            for value in values:
                target = value
                if isinstance(target, str):
                    target = ont_class.namespace.world.search_one(iri=str(value))
                if not isinstance(target, ThingClass):
                    errors.append(
                        f"Edge class {ont_class.iri} {ann_name} value {value} "
                        f"is not a URI resource resolving to a class")
                    continue
                if not require_node:
                    continue
                target_ancestors = {a.name for a in target.ancestors()}
                if "VITAL_Node" not in target_ancestors:
                    errors.append(
                        f"Edge class {ont_class.iri} {ann_name} value {target.iri} "
                        f"is not a VITAL_Node subclass")

        return errors

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
            return "LongProperty"
        elif range_iri == str(XSD.double):
            return "DoubleProperty"
        elif range_iri == str(XSD.float):
            return "FloatProperty"
        elif range_iri == str(XSD.dateTime):
            return "DateTimeProperty"
        elif range_iri == "http://vital.ai/ontology/vital-core#geoLocation":
            return "GeoLocationProperty"
        elif range_iri == "http://vital.ai/ontology/vital-core#truth":
            return "TruthProperty"
        elif range_iri == str(XSD.anyURI):
            # NOTE: parity spec table says URIProperty but this is unverified
            # against the committed corpus (no anyURI-ranged property in
            # vital-core); left as StringProperty until settled.
            return "StringProperty"
        else:
            # Unknown/custom range -> OtherProperty (Groovy behavior).
            return "OtherProperty"

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
            # Unknown/custom range -> OtherProperty in the .py, 'str' in the
            # .pyi (Groovy mapping table, other/unknown row).
            return "str"

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

