import threading
import time
from concurrent.futures import as_completed, ThreadPoolExecutor

from datetime import datetime
from rdflib import URIRef, Graph, Dataset, Literal, Namespace

from test_scripts.construct_query import ConstructQuery
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.service.graph.binding import Binding, BindingValueType
from vital_ai_vitalsigns.service.graph.memory.memory_graph_service import MemoryGraphService
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns.block.vital_block_file import VitalBlockFile
from vital_ai_vitalsigns.block.vital_block_reader import VitalBlockReader
# from rdflib.plugins.stores.berkeleydb import has_bsddb

import cProfile
import pstats
import io
import requests

from vital_ai_vitalsigns_core.model.RDFStatement import RDFStatement


wordnet_graph_uri = "urn:wordnet_graph"

lock = threading.Lock()


fuseki_url = 'http://localhost:3030'
dataset = 'graph'


def insert_triples_to_fuseki(triples, graph_uri, fuseki_url, dataset, batch_size=100000):
    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    for i, chunk in enumerate(chunker(triples, batch_size)):
        # Create a new RDF dataset
        d = Dataset()

        # Create a graph within the dataset with the given graph URI
        graph = d.graph(graph_uri)

        # Add triples to the graph
        for s, p, o in chunk:
            # print(s, p, o)
            graph.add((s, p, o))

        # Serialize the dataset to N-Quads format
        nquads_data = d.serialize(format='nquads')

        # Construct the endpoint URL for the dataset
        endpoint_url = f'{fuseki_url}/{dataset}/data'

        # Make the request to the Fuseki server
        response = requests.post(
            endpoint_url,
            data=nquads_data,
            headers={'Content-Type': 'application/n-quads'}
        )

        # Check the response status
        if response.status_code == 200:
            print(f'Batch {i + 1}: RDF data successfully imported into Fuseki.')
        else:
            print(f'Batch {i + 1}: Failed to import RDF data. Status code: {response.status_code}')
            print(response.text)



def generate_connecting_frame_query(entity_description: str):
    namespace_list = get_default_namespace_list()

    binding_list = [
        Binding("?uri", "urn:hasUri"),

        # Binding("?frame", "urn:hasFrame"),
        #Binding("?sourceSlot", "urn:hasSourceSlot"),
        #Binding("?destinationSlot", "urn:hasDestinationSlot"),
        #Binding("?sourceSlotEntity", "urn:hasSourceSlotEntity"),
        #Binding("?destinationSlotEntity", "urn:hasDestinationSlotEntity")


        # Binding("?prop", "urn:hasPropertyUri"),
        # Binding("?value", "urn:hasValue"),


    ]

    frame_query = f"""
        ?uri a haley-ai-kg:KGEntity ;
        haley-ai-kg:hasKGraphDescription ?description .
        FILTER(REGEX(?description, "{entity_description}", "i"))
        
        """

    """
            ?uri a haley-ai-kg:KGEntity .

    haley-ai-kg:hasKGraphDescription ?description .
        FILTER(REGEX(?description, "{entity_description}", "i"))
    
           ?uri a haley-ai-kg:KGEntity .

    haley-ai-kg:hasKGraphDescription ?description .
            FILTER(REGEX(?description, "{entity_description}", "i"))
       {{
         ?sourceEdge a haley-ai-kg:Edge_hasKGSlot ;
                     vital-core:hasEdgeSource ?frame ;
                     vital-core:hasEdgeDestination ?sourceSlot .
         ?sourceSlot a haley-ai-kg:KGEntitySlot ;
                     haley-ai-kg:hasEntitySlotValue ?uri ;
                     haley-ai-kg:hasKGSlotType <urn:hasSourceEntity> .
         ?destinationEdge a haley-ai-kg:Edge_hasKGSlot ;
                          vital-core:hasEdgeSource ?frame ;
                          vital-core:hasEdgeDestination ?destinationSlot .
         ?destinationSlot a haley-ai-kg:KGEntitySlot ;
                          haley-ai-kg:hasEntitySlotValue ?destinationSlotEntity ;
                          haley-ai-kg:hasKGSlotType <urn:hasDestinationEntity> .
         BIND(?uri AS ?sourceSlotEntity)
       }}
       UNION
       {{
         ?destinationEdge a haley-ai-kg:Edge_hasKGSlot ;
                          vital-core:hasEdgeSource ?frame ;
                          vital-core:hasEdgeDestination ?destinationSlot .
         ?destinationSlot a haley-ai-kg:KGEntitySlot ;
                          haley-ai-kg:hasEntitySlotValue ?uri ;
                          haley-ai-kg:hasKGSlotType <urn:hasDestinationEntity> .
         ?sourceEdge a haley-ai-kg:Edge_hasKGSlot ;
                     vital-core:hasEdgeSource ?frame ;
                     vital-core:hasEdgeDestination ?sourceSlot .
         ?sourceSlot a haley-ai-kg:KGEntitySlot ;
                     haley-ai-kg:hasEntitySlotValue ?sourceSlotEntity ;
                     haley-ai-kg:hasKGSlotType <urn:hasSourceEntity> .
         BIND(?uri AS ?destinationSlotEntity)
       }}
       """

    construct_query = ConstructQuery(namespace_list, binding_list, frame_query)

    return construct_query


def get_default_namespace_list():
    namespace_list = [
        Ontology("vital-core", "http://vital.ai/ontology/vital-core#"),
        Ontology("vital", "http://vital.ai/ontology/vital#"),
        Ontology("vital-aimp", "http://vital.ai/ontology/vital-aimp#"),
        Ontology("haley", "http://vital.ai/ontology/haley"),
        Ontology("haley-ai-question", "http://vital.ai/ontology/haley-ai-question#"),
        Ontology("haley-ai-kg", "http://vital.ai/ontology/haley-ai-kg#")
    ]

    return namespace_list


def triple_count(dataset: Dataset) -> int:
    total_triples = 0

    for graph in dataset.contexts():
        graph_triples_count = len(graph)
        total_triples += graph_triples_count

    return total_triples


def process_par_reader(memory_service, par_reader):
    try:
        print(f"Worker{par_reader.num} started processing.")

        pr = cProfile.Profile()
        pr.enable()

        now_time = datetime.now()

        obj_count = 0

        # data_graph = Dataset()

        triple_list = []

        for block in par_reader:

            go = block.first_object

            # print(go.to_rdf())

            go_list = block.rest_objects
            object_list = [go]
            object_list.extend(go_list)
            for go in object_list:
                obj_count += 1
                if obj_count % 1000 == 0:
                    # print(f"Worker{par_reader.num} Object Count: {obj_count}.")
                    pass
                # go.add_to_dataset(data_graph, graph_uri=wordnet_graph_uri)
                # print(f"Worker{par_reader.num} Triple Count: {triple_count(data_graph)}")
                go.add_to_list(triple_list)

        print(f"Worker{par_reader.num} Entering Lock.")

        with lock:

            wordnet_graph = memory_service.graph.get_graph(URIRef(wordnet_graph_uri))

            block_now_time = datetime.now()

            print(f"Worker{par_reader.num} Blocking.")

            # wordnet_graph += data_graph
            # for s, p, o, g in data_graph:
            #    wordnet_graph.add((s, p, o))

            print(f"Worker{par_reader.num} Dataset Triples Before: {triple_count(memory_service.graph)}")

            print(f"Worker{par_reader.num} Dataset Adding Triples: {len(triple_list)}")

            print(f"Worker{par_reader.num} Triples: {triple_list[:100]}")

            # for s, o, p in triple_list:
            #    wordnet_graph.add((s, p, o))

            print(f"Worker{par_reader.num} Dataset Triples After: {triple_count(memory_service.graph)}")

            block_current_time = datetime.now()
            block_delta_time = block_current_time - block_now_time

            print(f"Worker{par_reader.num} Releasing. Delta: {block_delta_time}")

        print(f"Worker{par_reader.num} finished processing.")
        print(f"Worker{par_reader.num} Object count: {obj_count}")

        current_time = datetime.now()
        delta_time = current_time - now_time

        print(f"Worker{par_reader.num} Done Processing in {delta_time}")

        pr.disable()

        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()

        profiling_results = s.getvalue()
        print(profiling_results)

        return obj_count

    except Exception as e:
        print(f"Worker exception: {e}")
        raise


def process_par_reader_triples(memory_service, par_reader):
    try:
        print(f"Worker{par_reader.num} started triples processing.")

        # pr = cProfile.Profile()
        # pr.enable()

        now_time = datetime.now()

        triple_list = []

        total_triple_count = 0

        for block in par_reader:

            triples = block.get_triples()

            for triple in triples:
                # print(triple)
                total_triple_count += 1
                triple_list.append(triple)

        print(f"Worker{par_reader.num} Entering Lock.")

        with lock:

            wordnet_graph = memory_service.graph.get_graph(URIRef(wordnet_graph_uri))

            block_now_time = datetime.now()

            print(f"Worker{par_reader.num} Blocking.")

            print(f"Worker{par_reader.num} Dataset Triples Before: {triple_count(memory_service.graph)}")

            print(f"Worker{par_reader.num} Dataset Adding Triples: {len(triple_list)}")

            # print(f"Worker{par_reader.num} Triples: {triple_list[:100]}")

            for s, p, o in triple_list:
                # wordnet_graph.add((s, p, o))
                # memory_service.store.add((s, p, o), URIRef(wordnet_graph_uri))
                pass

            insert_triples_to_fuseki(triple_list, wordnet_graph_uri, fuseki_url, dataset)

            # store_count = len(memory_service.store)

            # print(f"Worker{par_reader.num} Store Count After: {store_count}")

            print(f"Worker{par_reader.num} Dataset Triples After: {triple_count(memory_service.graph)}")

            block_current_time = datetime.now()
            block_delta_time = block_current_time - block_now_time

            print(f"Worker{par_reader.num} Releasing. Delta: {block_delta_time}")

        print(f"Worker{par_reader.num} finished processing.")

        current_time = datetime.now()
        delta_time = current_time - now_time

        print(f"Worker{par_reader.num} Done Processing in {delta_time}")

        # pr.disable()

        # s = io.StringIO()
        # sortby = 'cumulative'
        # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        # ps.print_stats()

        # profiling_results = s.getvalue()
        # print(profiling_results)

        return total_triple_count

    except Exception as e:
        print(f"Worker exception: {e}")
        raise


def main():
    print('Test Memory Service Parallel')

    print("VitalSigns Initializing...")

    vs = VitalSigns()

    print("VitalSigns Initialized")

    memory_service = MemoryGraphService()

    VITAL_CORE = Namespace("http://vital.ai/ontology/vital-core#")
    VITAL = Namespace("http://vital.ai/ontology/vital#")
    VITAL_AIMP = Namespace("http://vital.ai/ontology/vital-aimp#")
    HALEY = Namespace("http://vital.ai/ontology/haley")
    HALEY_AI_QUESTION = Namespace("http://vital.ai/ontology/haley-ai-question#")
    HALEY_AI_KG = Namespace("http://vital.ai/ontology/haley-ai-kg#")

    # Bind namespaces to the dataset
    memory_service.graph.bind("vital-core", VITAL_CORE)
    memory_service.graph.bind("vital", VITAL)
    memory_service.graph.bind("vital-aimp", VITAL_AIMP)
    memory_service.graph.bind("haley", HALEY)
    memory_service.graph.bind("haley-ai-question", HALEY_AI_QUESTION)
    memory_service.graph.bind("haley-ai-kg", HALEY_AI_KG)

    name_graph_list = memory_service.list_graphs()

    for ng in name_graph_list:
        print(f"Name Graph: {ng}")

    print(f"Creating new graph: {wordnet_graph_uri}")

    created = memory_service.create_graph(wordnet_graph_uri)

    # input_file_path = '../test_data/kgframe-wordnet-0.0.1.vital.bz2'

    input_file_path = '../test_data/kgframe-wordnet-0.0.1.vital'

    block_file = VitalBlockFile(input_file_path)

    read_file = VitalBlockReader(block_file, triples_only=True)

    parallel_list = read_file.get_parallel_readers(5)

    print(f"Parallel readers: {len(parallel_list)}")

    obj_count = 0

    initial_start_time = datetime.now()

    with ThreadPoolExecutor(max_workers=100) as executor:

        futures = [executor.submit(process_par_reader_triples, memory_service, par_reader) for par_reader in parallel_list]

        for future in as_completed(futures):
            try:
                result = future.result()
                print(f"Completed processing par_reader: {result}")
                worker_count = result

                obj_count += worker_count

            except Exception as e:
                print(f"Exception encountered while processing future: {e}")
                raise

        total_triples = 0

    # memory_service.graph.commit()

    for graph in memory_service.graph.contexts():
        graph_triples_count = len(graph)
        print(f"Identifier: {graph.identifier} Count: {graph_triples_count}")
        total_triples += graph_triples_count

    print(f"Inserted {obj_count} objects")

    current_time = datetime.now()
    delta_time = current_time - initial_start_time
    # print(f"Inserted {obj_count:,} objects in {delta_time}")
    print(f"Inserted triples {total_triples:,} in {delta_time}")

    name_graph_list = memory_service.list_graphs()

    for ng in name_graph_list:
        print(f"Name Graph: {ng}")

    search_string = "happy"

    # Query:
    # kg entity: description contains search string
    # --source--> frame --destination--> other entity
    # or
    # kg entity: description contains search string
    # <--destination-- frame <--source-- other entity

    construct_query = generate_connecting_frame_query(search_string)

    """
    solutions = vital_graph_service.query_construct_solution(
    wordnet_frame_graph_uri,
    construct_query.query,
    construct_query.namespace_list,
    construct_query.binding_list,
    construct_query.root_binding,
    limit=500, offset=0)

    print(f"Wordnet Solution Count: {len(solutions.solution_list)}")

    for solution in solutions.solution_list:
        for binding, obj in solution.object_map.items():
            binding_uri = solution.uri_map[binding]
            print(f"Wordnet Solution Binding: {binding} : {binding_uri}")
            print(obj.to_rdf())

    """

    start_time = time.time()

    result_list = memory_service.query_construct(
        wordnet_graph_uri,
        construct_query.query,
        construct_query.namespace_list,
        construct_query.binding_list,
        limit=10, offset=0
    )

    print(result_list)
    for r in result_list:
        print(r)

    end_time = time.time()
    delta_time = end_time - start_time
    print(f"Time taken for the frame construct query: {delta_time:.2f} seconds")

    graph = Graph()

    for result in result_list:
        rs = result.graph_object
        if isinstance(rs, RDFStatement):
            s = rs.rdfSubject
            p = rs.rdfPredicate

            value_type = BindingValueType.URIREF

            for binding in construct_query.binding_list:
                if binding.property_uri == str(p):
                    value_type = binding.value_type
                    break

            o = rs.rdfObject
            if value_type == BindingValueType.URIREF:
                graph.add((URIRef(str(s)), URIRef(str(p)), URIRef(str(o))))
            else:
                graph.add((URIRef(str(s)), URIRef(str(p)), Literal(str(o))))

    subjects = set(graph.subjects())
    num_unique_subjects = len(subjects)

    print(f"Wordnet Solution Count: {num_unique_subjects}")

    subject_set = set()

    for triple in graph.triples((None, None, None)):
        [s, p, o] = triple

        if p == URIRef("urn:hasUri"):
            subject_set.add((str(o)))

        if p == URIRef("urn:hasFrame"):
            subject_set.add((str(o)))

        if p == URIRef("urn:hasSourceSlotEntity"):
            subject_set.add((str(o)))

        if p == URIRef("urn:hasDestinationSlotEntity"):
            subject_set.add((str(o)))

    print(f"Getting objects count: {len(subject_set)}")

    start_time = time.time()

    result_list = memory_service.get_object_list(
        list(subject_set),
        graph_uri=wordnet_graph_uri)

    end_time = time.time()
    delta_time = end_time - start_time
    print(f"Time taken for the bulk retrieval: {delta_time:.2f} seconds")

    # print(result_list)

    graph_object_list = []

    for obj in result_list:
        go = obj.graph_object
        graph_object_list.append(go)
        # print(go.to_rdf())

    print(f"Got objects count: {len(graph_object_list)}")


if __name__ == "__main__":
    # if not has_bsddb:
    #    print("No DB!")

    main()
