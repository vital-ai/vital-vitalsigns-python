import gzip
import json
import uuid
import weaviate
from com_vitalai_domain_wordnet.model.Edge_hasWordnetPointer import Edge_hasWordnetPointer
from com_vitalai_domain_wordnet.model.SynsetNode import SynsetNode
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from weaviate.config import AdditionalConfig, Timeout
from weaviate.connect import ConnectionParams
import weaviate.classes.config as wvcc
from rdflib import URIRef
from rdflib.namespace import split_uri
from weaviate.classes.query import Filter


reference_list = [
    "edge_WordnetAlsoSee",
    "edge_WordnetAntonym",
    "edge_WordnetAttribute",
    "edge_WordnetCause",
    "edge_WordnetDerivationallyRelatedForm",
    "edge_WordnetDerivedFromAdjective",
    "edge_WordnetDomainOfSynset_Region",
    "edge_WordnetDomainOfSynset_Topic",
    "edge_WordnetDomainOfSynset_Usage",
    "edge_WordnetEntailment",
    "edge_WordnetHypernym",
    "edge_WordnetHyponym",
    "edge_WordnetInstanceHypernym",
    "edge_WordnetInstanceHyponym",
    "edge_WordnetMemberHolonym",
    "edge_WordnetMemberMeronym",
    "edge_WordnetMemberOfThisDomain_Region",
    "edge_WordnetMemberOfThisDomain_Topic",
    "edge_WordnetMemberOfThisDomain_Usage",
    "edge_WordnetPartHolonym",
    "edge_WordnetParticiple",
    "edge_WordnetPartMeronym",
    "edge_WordnetPertainym_PertainsToNouns",
    "edge_WordnetSimilarTo",
    "edge_WordnetSubstanceHolonym",
    "edge_WordnetSubstanceMeronym",
    "edge_WordnetVerbGroup"
]


def main():
    print('Weaviate Wordnet Import')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    tenant_id = "wordnet-graph-1"
    graph_uri = "http://vital.ai/graph/wordnet-graph-1"

    vitalservice_manager = vs.get_vitalservice_manager()

    vitalservice_name_list = vitalservice_manager.get_vitalservice_list()

    for vitalservice_name in vitalservice_name_list:
        vitalservice = vitalservice_manager.get_vitalservice(vitalservice_name)
        print(f"VitalService Name: {vitalservice.get_vitalservice_name()}")

    vitalservice = vitalservice_manager.get_vitalservice("local_kgraph")

    graph_list = vitalservice.list_graphs(account_id="account1")

    for g in graph_list:
        print(f"Graph URI: {g.get_namespace()}")

    weaviate_endpoint = vitalservice.vector_service.endpoint
    weaviate_grpc_endpoint = vitalservice.vector_service.grpc_endpoint
    weaviate_vector_endpoint = vitalservice.vector_service.vector_endpoint

    client = weaviate.WeaviateClient(
        connection_params=ConnectionParams.from_params(
            http_host=weaviate_endpoint,
            http_port=8080,
            http_secure=False,
            grpc_host=weaviate_grpc_endpoint,
            grpc_port=50051,
            grpc_secure=False,
        ),

        additional_config=AdditionalConfig(
            timeout=Timeout(init=20, query=45, insert=120),
        ),
    )

    client.connect()

    meta_info = client.get_meta()

    print(meta_info)

    # collection wordnet nodes
    # collection wordnet edge
    # delete collections if present

    uuid_to_uri = {}
    uri_to_uuid = {}
    edge_map = {}

    try:

        # """
        try:
            synset_node = client.collections.get("SynsetNode")
            synset_node_config = synset_node.config.get()
            if synset_node_config:
                print(synset_node_config)
                client.collections.delete("SynsetNode")
                print("SynsetNode collection deleted.")
        except Exception as e:
            print(f"Exception getting/deleting SynsetNode: {e}")

        try:
            synset_edge = client.collections.get("Edge_hasWordnetPointer")
            synset_edge_config = synset_edge.config.get()
            if synset_edge_config:
                print(synset_edge_config)
                client.collections.delete("Edge_hasWordnetPointer")
                print("Edge_hasWordnetPointer collection deleted")
        except Exception as e:
            print(f"Exception getting/deleting Edge_hasWordnetPointer: {e}")

        node_property_list = [
            wvcc.Property(
                name="uRI",
                data_type=wvcc.DataType.TEXT,
                skip_vectorization=True
            ),
            wvcc.Property(
                name="hasName",
                data_type=wvcc.DataType.TEXT
            ),
            wvcc.Property(
                name="hasGloss",
                data_type=wvcc.DataType.TEXT
            ),
            wvcc.Property(
                name="hasWordnetID",
                data_type=wvcc.DataType.TEXT,
                skip_vectorization=True
            ),
            wvcc.Property(
                name="subclassURI",
                data_type=wvcc.DataType.TEXT,
                skip_vectorization=True
            )
        ]

        # defined as:
        # SynsetNode ---> SynsetNode
        # the edges on OWL are be defined more specifically like:
        # Noun --> Noun, but we're not making that distinction here
        # the GraphQL will need to enforce that by filtering for subclass URIs

        reference_property_list = []

        for r in reference_list:
            ref = wvcc.ReferenceProperty(
                name=r,
                target_collection="SynsetNode"
            )

            reference_property_list.append(ref)

        synset_node_collection = client.collections.create(
            name="SynsetNode",
            vectorizer_config=wvcc.Configure.Vectorizer.text2vec_transformers(),
            properties=node_property_list,
            references=reference_property_list
        )

        synset_edge_collection = client.collections.create(
            name="Edge_hasWordnetPointer",
            vectorizer_config=wvcc.Configure.Vectorizer.text2vec_transformers(),
            properties=[
                wvcc.Property(
                    name="uRI",
                    data_type=wvcc.DataType.TEXT,
                    skip_vectorization=True
                ),
                wvcc.Property(
                    name="sourceURI",
                    data_type=wvcc.DataType.TEXT,
                    skip_vectorization=True
                ),
                wvcc.Property(
                    name="destinationURI",
                    data_type=wvcc.DataType.TEXT,
                    skip_vectorization=True
                ),
                wvcc.Property(
                    name="subclassURI",
                    data_type=wvcc.DataType.TEXT,
                    skip_vectorization=True
                ),
                wvcc.Property(
                    name="reference_uuid",
                    data_type=wvcc.DataType.UUID
                )
            ]
        )
        # """

        synset_node_collection = client.collections.get("SynsetNode")
        synset_edge_collection = client.collections.get("Edge_hasWordnetPointer")

        print(f"Node collection Size: {len(synset_node_collection)}")
        print(f"Edge collection Size: {len(synset_edge_collection)}")

        response = client.collections.list_all(simple=False)

        print(response)

        input_file_path = '../test_data/wordnet-0.0.1.jsonl.gz'

        # """

        read_file = gzip.open(input_file_path, 'rt', encoding='utf-8')

        count = 0

        with synset_node_collection.batch.fixed_size(batch_size=1000) as batch:

            try:
                for line in read_file:

                    # data = json.loads(line)

                    go = vs.from_json(line)

                    # Node case
                    if isinstance(go, SynsetNode):

                        go_uuid = str(uuid.uuid4())

                        uri_to_uuid[str(go.URI)] = go_uuid
                        uuid_to_uri[go_uuid] = str(go.URI)

                        subclass_uri = go.get_class_uri()

                        properties = {
                            "uRI": str(go.URI),
                            "hasName": str(go.name),
                            "hasGloss": str(go.gloss),
                            "hasWordnetID": str(go.wordnetID),
                            "subclassURI": subclass_uri
                        }

                        batch.add_object(
                            properties=properties,
                            uuid=go_uuid
                        )

                        count += 1

                        print(f"Node Count: {count}")

            finally:
                read_file.close()

        # """

        # """
        read_file = gzip.open(input_file_path, 'rt', encoding='utf-8')

        count = 0

        # split loading edges into separate pass?
        # for some reason really slow.

        # change to looking up ref in node via URI instead of
        # keeping maps; do refs in separate pass.

        with synset_edge_collection.batch.fixed_size(batch_size=1000) as batch:

            try:
                for line in read_file:

                    # data = json.loads(line)

                    go = vs.from_json(line)

                    # Edge case
                    if isinstance(go, Edge_hasWordnetPointer):

                        go_uuid = str(uuid.uuid4())

                        # uri_to_uuid[str(go.URI)] = go_uuid
                        # uuid_to_uri[go_uuid] = str(go.URI)
                        # edge_map[str(go.URI)] = go

                        subclass_uri = go.get_class_uri()

                        properties = {
                            "uRI": str(go.URI),
                            "sourceURI": str(go.edgeSource),
                            "destinationURI": str(go.edgeDestination),
                            "subclassURI": subclass_uri
                        }

                        batch.add_object(
                            properties=properties,
                            uuid=go_uuid
                        )

                        count += 1
                        print(f"Edge Count: {count}")

            finally:
                read_file.close()

        # """

        # """
        # add references
        
        read_file = gzip.open(input_file_path, 'rt', encoding='utf-8')

        count = 0

        with synset_node_collection.batch.fixed_size(batch_size=1000) as batch:

            try:
                for line in read_file:

                    go = vs.from_json(line)

                    if isinstance(go, Edge_hasWordnetPointer):
                    
                        edge = go
                    
                        source_uri = str(edge.edgeSource)

                        destination_uri = str(edge.edgeDestination)

                        source_uuid = get_object_uuid(source_uri, synset_node_collection)
                        destination_uuid = get_object_uuid(destination_uri, synset_node_collection)

                        edge_class_uri = edge.get_class_uri()

                        # http://vital.ai/ontology/vital-wordnet#Edge_WordnetAlsoSee
                        # Edge_WordnetAlsoSee

                        uri_ref = URIRef(edge_class_uri)

                        namespace, local_part = split_uri(uri_ref)

                        local_part = lowercase_first_letter(local_part)

                        batch.add_reference(
                            from_property=local_part,
                            from_uuid=source_uuid,
                            to=destination_uuid
                        )

                        count += 1
                        print(f"Reference Count: {count}")

            finally:
                read_file.close()

        # """

    except Exception as e:
        print(f"Exception creating collections: {e}")

    finally:
        print(f"Node collection Ending Size: {len(synset_node_collection)}")
        print(f"Edge collection Ending Size: {len(synset_edge_collection)}")

        client.close()


def get_object_uuid(object_uri: str, collection):

    response = collection.query.fetch_objects(
        filters=Filter.by_property("uRI").equal(object_uri),
        limit=1
    )

    for obj in response.objects:
        go_uuid = obj.uuid
        return go_uuid

    return None


def lowercase_first_letter(s):
    if not s:
        return s  # return the string as is if it is empty
    return s[0].lower() + s[1:]


def convert_node_object():
    pass


def convert_edge_object():
    pass


if __name__ == "__main__":
    main()

