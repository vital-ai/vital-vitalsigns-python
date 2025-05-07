from vital_ai_vitalsigns.vitalsigns import VitalSigns

def main():

    print('Test Ontology Manager Subclass List')

    vs = VitalSigns()

    domain_graph = vs.get_ontology_manager().get_domain_graph()

    class_query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX vital: <http://vital.ai/ontology/vital-core#>
        PREFIX haley-ai-kg: <http://vital.ai/ontology/haley-ai-kg#>

        SELECT ?class ?label ?parent
        WHERE {
            ?class rdfs:subClassOf* vital:VITAL_Node .

            OPTIONAL { ?class rdfs:label ?label }
            OPTIONAL { ?class rdfs:subClassOf ?parent }
        }
        """

    results = domain_graph.query(class_query)

    for row in results:
        class_uri = str(row['class'])
        label = str(row['label']) if row['label'] else class_uri.split('#')[-1]
        parent_uri = str(row['parent']) if row['parent'] else None

        print(f"Class URI: {class_uri}, Label: {label}, Parent URI: {parent_uri}")


if __name__ == "__main__":
    main()
