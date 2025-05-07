from vital_ai_vitalsigns.block.vital_block_file import VitalBlockFile
from vital_ai_vitalsigns.block.vital_block_reader import VitalBlockReader
from vital_ai_vitalsigns.vitalsigns import VitalSigns


def main():

    print('Convert Block To NTriples')

    input_file_path = '../test_data/kgframe-wordnet-0.0.1.vital.bz2'

    output_file_path = '../test_data/kgframe-wordnet-0.0.2.nt'

    vs = VitalSigns()

    block_file = VitalBlockFile(input_file_path)

    read_file = VitalBlockReader(block_file)

    write_file = open(output_file_path, 'w', encoding='utf-8')

    try:

        for block in read_file:

            go = block.first_object
            go_list = block.rest_objects

            object_list = [go]

            for g in go_list:
                object_list.append(g)

            for g in object_list:
                triples = g.to_rdf()

                # print(triples)

                write_file.write(triples)

    finally:
        write_file.close()


if __name__ == "__main__":
    main()
