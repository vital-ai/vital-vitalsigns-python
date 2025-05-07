import threading
from concurrent.futures import as_completed, ThreadPoolExecutor

import dill

# mp.set_start_method('spawn', force=True)

from datetime import datetime
from rdflib import URIRef, Graph
from vital_ai_vitalsigns.service.graph.memory.memory_graph_service import MemoryGraphService
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns.service.graph.graph_service_constants import VitalGraphServiceConstants
from vital_ai_vitalsigns.block.vital_block_file import VitalBlockFile
from vital_ai_vitalsigns.block.vital_block_reader import VitalBlockReader
from multiprocessing import Pool
import traceback


def parse_reader(par_reader):
    try:
        print("Worker started processing.")

        graph = Graph()
        obj_count = 0

        for block in par_reader:
            go = block.first_object
            go_list = block.rest_objects
            object_list = [go]
            object_list.extend(go_list)
            for go in object_list:
                obj_count += 1
                go.add_to_graph(graph)

        graph_str = graph.serialize(format='nt')
        print("Worker finished processing.")
        print(f"Worker Object count: {obj_count}")
        print(f"Worker graph size: {len(graph_str)}")
        return graph_str
    except Exception as e:
        print(f"Worker exception: {e}")
        raise


def parallel_process_reader(par_reader_serialized):
    par_reader = dill.loads(par_reader_serialized)
    return dill.dumps(parse_reader(par_reader))


def main():
    print('Test Memory Service')

    print("VitalSigns Initializing...")

    vs = VitalSigns()

    print("VitalSigns Initialized")

    memory_service = MemoryGraphService()

    name_graph_list = memory_service.list_graphs()

    for ng in name_graph_list:
        print(f"Name Graph: {ng}")

    new_graph = "urn:new_graph"

    print(f"Creating new graph: {new_graph}")

    created = memory_service.create_graph(new_graph)

    name_graph_list = memory_service.list_graphs()

    for ng in name_graph_list:
        print(f"Name Graph: {ng}")

    service_graph = memory_service.graph.get_graph(URIRef(VitalGraphServiceConstants.SERVICE_GRAPH_URI))

    for subject, predicate, obj in service_graph:
        print(f"Subject: {subject}, Predicate: {predicate}, Object: {obj}")

    print(f"Deleting new graph: {new_graph}")

    deleted = memory_service.delete_graph(new_graph)

    name_graph_list = memory_service.list_graphs()

    for ng in name_graph_list:
        print(f"Name Graph: {ng}")

    service_graph = memory_service.graph.get_graph(URIRef(VitalGraphServiceConstants.SERVICE_GRAPH_URI))

    for subject, predicate, obj in service_graph:
        print(f"Subject: {subject}, Predicate: {predicate}, Object: {obj}")

    wordnet_graph_uri = "urn:wordnet_graph"

    print(f"Creating new graph: {wordnet_graph_uri}")

    created = memory_service.create_graph(wordnet_graph_uri)

    # input_file_path = '../test_data/kgframe-wordnet-0.0.1.vital.bz2'

    input_file_path = '../test_data/kgframe-wordnet-0.0.1.vital'

    block_file = VitalBlockFile(input_file_path)

    read_file = VitalBlockReader(block_file)

    parallel_list = read_file.get_parallel_readers(10)

    print(f"Parallel readers: {len(parallel_list)}")

    obj_count = 0

    initial_start_time = datetime.now()

    # start_time = datetime.now()

    # update to pass the parameters of a reader and then create the reader in the process
    # use different start process methods like spawn

    lock = threading.Lock()

    with Pool(processes=10) as pool:

        futures = [pool.apply_async(parallel_process_reader, args=(dill.dumps(par_reader),)) for par_reader in parallel_list]

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_obj = {executor.submit(future.get): future for future in futures}

            for future in as_completed(future_to_obj):

                try:
                    # object_list = future.get()
                    # object_list_serialized = future.get()
                    # object_list = dill.loads(object_list_serialized)

                    graph_str_serialized = future.result()
                    graph_str = dill.loads(graph_str_serialized)

                    print(f"Processing Graph String Size: {len(graph_str)}")

                    wordnet_graph = memory_service.graph.get_graph(URIRef(wordnet_graph_uri))

                    data_graph = Graph()

                    print(f"Parsing Graph String Size: {len(graph_str)}")

                    now_time = datetime.now()

                    data_graph.parse(data=graph_str, format='nt')

                    with lock:
                        wordnet_graph += data_graph

                    current_time = datetime.now()
                    delta_time = current_time - now_time

                    print(f"Done Processing Graph String Size: {len(graph_str)} in {delta_time}")

                    # memory_service.insert_object_list(wordnet_graph, object_list)
                    # obj_count += len(object_list)

                except Exception as e:
                    print(f"Exception encountered: {e}")
                    traceback.print_exc()
                    raise

        total_triples = 0

        for graph in memory_service.graph.contexts():
            graph_triples_count = len(graph)
            total_triples += graph_triples_count

        # print(f"Inserted {obj_count} objects")

        current_time = datetime.now()
        delta_time = current_time - initial_start_time
        # print(f"Inserted {obj_count:,} objects in {delta_time}")
        print(f"Inserted triples {total_triples:,} in {delta_time}")

    def old():

        obj_count = 0
        parallel_list = []

        for par_reader in parallel_list:

            # for block in read_file:

            print(f"Par reader: {par_reader}")

            for block in par_reader:

                go = block.first_object
                go_list = block.rest_objects

                object_list = [go]

                for g in go_list:
                    object_list.append(g)

                # memory_service.insert_object_list(wordnet_graph, object_list)

                for g in object_list:
                    # triples = g.to_rdf()
                    # print(triples)
                    # memory_service.insert_object(wordnet_graph, g)
                    obj_count += 1

                    if obj_count % 10000 == 0:
                        current_time = datetime.now()
                        delta_time = current_time - start_time
                        start_time = current_time
                        print(f"Inserted {obj_count:,} objects in {delta_time}")


if __name__ == "__main__":
    main()
