import gzip
import json
from vital_ai_vitalsigns.vitalsigns import VitalSigns


def main():
    print('Test Wordnet Convert')

    vs = VitalSigns()

    input_file_path = '../test_data/wordnet-0.0.1.jsonl.gz'
    output_file_path = '../test_data/wordnet-0.0.1.nt'

    read_file = gzip.open(input_file_path, 'rt', encoding='utf-8')
    write_file = open(output_file_path, 'w', encoding='utf-8')

    try:
        for line in read_file:
            data = json.loads(line)
            print(data)

            go = vs.from_json(line)

            triples = go.to_rdf()

            print(triples)

            write_file.write(triples)

    finally:
        read_file.close()
        write_file.close()


if __name__ == "__main__":
    main()
