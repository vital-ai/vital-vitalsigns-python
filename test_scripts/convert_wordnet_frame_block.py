import gzip
import json
from urllib.parse import urlparse
import psutil
from ai_haley_kg_domain.model.Edge_hasKGSlot import Edge_hasKGSlot
from ai_haley_kg_domain.model.KGEntity import KGEntity
from ai_haley_kg_domain.model.KGEntitySlot import KGEntitySlot
from ai_haley_kg_domain.model.KGFrame import KGFrame
from vital_ai_vitalsigns.block.vital_block import VitalBlock
from vital_ai_vitalsigns.block.vital_block_file import VitalBlockFile
from vital_ai_vitalsigns.block.vital_block_writer import VitalBlockWriter
from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns


def main():

    print('Convert Wordnet Frame Block')

    input_file_path = '../test_data/wordnet-0.0.1.jsonl.gz'
    output_file_path = '../test_data/kgframe-wordnet-0.0.1.vital.bz2'

    vs = VitalSigns()

    read_file = gzip.open(input_file_path, 'rt', encoding='utf-8')

    wordnet = {}

    kgentity_map = {}

    try:
        for line in read_file:
            data = json.loads(line)
            # print(data)

            go = vs.from_json(line)

            uri = str(go.URI)

            wordnet[uri] = go

            # triples = go.to_rdf()
            # print(triples)

    finally:
        read_file.close()

    count = len(wordnet)

    print(f"Wordnet Count: {count}")

    # process = psutil.Process()
    # memory_info = process.memory_info()
    # memory_usage_in_bytes = memory_info.rss
    # # Convert to megabytes
    # memory_usage_in_megabytes = memory_usage_in_bytes / (1024 ** 2)
    # print(f"Memory usage: {memory_usage_in_megabytes:.2f} MB")

    try:

        block_file = VitalBlockFile(output_file_path)

        write_file = VitalBlockWriter(block_file)

        write_file.write_header()

        for go in wordnet.values():

            if isinstance(go, VITAL_Edge):

                edge = go
                edge_uri = str(edge.URI)
                source_uri = str(edge.edgeSource)
                destination_uri = str(edge.edgeDestination)

                source_node = wordnet[source_uri]
                destination_node = wordnet[destination_uri]

                source_parsed_uri = urlparse(source_uri)
                source_last_part = source_parsed_uri.path.split('/')[-1]
                source_kgentity_uri = "http://vital.ai/haley.ai/app/KGEntity/" + source_last_part

                source_kgentity = kgentity_map.get(source_kgentity_uri)

                # add source kg entity based on source_node
                if source_kgentity is None:
                    source_type_uri = source_node.get_class_uri()
                    source_gloss = str(source_node.gloss)
                    source_wordnet_id = str(source_node.wordnetID)
                    source_name = str(source_node.name)

                    source_type_parsed_uri = urlparse(source_type_uri)
                    # fragment is the class name
                    source_type_last_part = source_type_parsed_uri.fragment

                    source_kgentity = KGEntity()
                    source_kgentity.URI = source_kgentity_uri
                    source_kgentity.name = source_name
                    source_kgentity.kGraphDescription = source_gloss
                    source_kgentity.kGIdentifier = f"urn:wordnet_{source_wordnet_id}"
                    source_kgentity.kGEntityType = f"urn:{source_type_last_part}"
                    source_kgentity.kGEntityTypeDescription = source_type_last_part
                    kgentity_map[source_kgentity_uri] = source_kgentity

                destination_parsed_uri = urlparse(destination_uri)
                destination_last_part = destination_parsed_uri.path.split('/')[-1]
                destination_kgentity_uri = "http://vital.ai/haley.ai/app/KGEntity/" + destination_last_part

                destination_kgentity = kgentity_map.get(destination_kgentity_uri)

                # add destination kg entity based on destination node
                if destination_kgentity is None:
                    destination_type_uri = destination_node.get_class_uri()
                    destination_gloss = str(destination_node.gloss)
                    destination_wordnet_id = str(destination_node.wordnetID)
                    destination_name = str(destination_node.name)

                    destination_type_parsed_uri = urlparse(destination_type_uri)
                    # fragment is the class name
                    destination_type_last_part = destination_type_parsed_uri.fragment

                    destination_kgentity = KGEntity()
                    destination_kgentity.URI = destination_kgentity_uri
                    destination_kgentity.name = destination_name
                    destination_kgentity.kGraphDescription = destination_gloss
                    destination_kgentity.kGIdentifier = f"urn:wordnet_{destination_wordnet_id}"
                    destination_kgentity.kGEntityType = f"urn:{destination_type_last_part}"
                    destination_kgentity.kGEntityTypeDescription = destination_type_last_part
                    kgentity_map[destination_kgentity_uri] = destination_kgentity

                # add frame based on edge
                # with slots

                edge_parsed_uri = urlparse(edge_uri)
                edge_last_part = edge_parsed_uri.path.split('/')[-1]
                kgframe_uri = "http://vital.ai/haley.ai/app/KGFrame/" + edge_last_part

                edge_type_uri = edge.get_class_uri()

                edge_type_parsed_uri = urlparse(edge_type_uri)
                # fragment is the class name
                edge_type_last_part = edge_type_parsed_uri.fragment

                # frame
                kgframe = KGFrame()
                kgframe.URI = kgframe_uri

                kgframe.kGFrameType = f"urn:{edge_type_last_part}"
                kgframe.kGFrameTypeDescription = edge_type_last_part

                # slot source entity

                source_slot = KGEntitySlot()
                source_slot.URI = URIGenerator.generate_uri()
                source_slot.kGSlotType = "urn:hasSourceEntity"
                source_slot.kGSlotTypeDescription = "hasSourceEntity"
                source_slot.entitySlotValue = source_kgentity_uri

                # slot destination entity

                destination_slot = KGEntitySlot()
                destination_slot.URI = URIGenerator.generate_uri()
                destination_slot.kGSlotType = "urn:hasDestinationEntity"
                destination_slot.kGSlotTypeDescription = "hasDestinationEntity"
                destination_slot.entitySlotValue = destination_kgentity_uri

                # source slot edge

                source_slot_edge = Edge_hasKGSlot()
                source_slot_edge.URI = URIGenerator.generate_uri()
                source_slot_edge.edgeSource = kgframe.URI
                source_slot_edge.edgeDestination = source_slot.URI

                # destination slot edge

                destination_slot_edge = Edge_hasKGSlot()
                destination_slot_edge.URI = URIGenerator.generate_uri()
                destination_slot_edge.edgeSource = kgframe.URI
                destination_slot_edge.edgeDestination = destination_slot.URI

                # vital_block = VitalBlock([go, source_kgentity, destination_kgentity])

                # output block for frame and slots
                vital_block = VitalBlock([
                    kgframe,
                    source_slot,
                    destination_slot,
                    source_slot_edge,
                    destination_slot_edge])

                write_file.write_block(vital_block)

        # output block for each kg entity
        for kgentity in kgentity_map.values():
            vital_block = VitalBlock([kgentity])
            write_file.write_block(vital_block)

    finally:
        write_file.close()


if __name__ == "__main__":
    main()
