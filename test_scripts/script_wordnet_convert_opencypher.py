import csv
import json
import sys
import gzip

# Define static file paths.
INPUT_FILE = "../test_data/wordnet-0.0.1.jsonl.gz"
NODES_OUTPUT = "../test_data/nodes.csv"
EDGES_OUTPUT = "../test_data/edges.csv"

def extract_label(type_value):
    # Extract the fragment after '#' if present; otherwise, take the part after the last '/'
    if not type_value:
        return "node"
    if '#' in type_value:
        return type_value.rsplit('#', 1)[-1]
    else:
        return type_value.rsplit('/', 1)[-1]


def open_input_file(filename):
    # Open file using gzip.open if the file ends with .gz; otherwise, use open.
    if filename.endswith(".gz"):
        return gzip.open(filename, 'rt', encoding='utf-8')
    else:
        return open(filename, 'r', encoding='utf-8')


def compute_field_keys():
    # We build separate sets of keys for nodes and edges.
    node_keys = set()
    edge_keys = set()
    with open_input_file(INPUT_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Skipping invalid JSON line: {line}\nError: {e}", file=sys.stderr)
                continue

            # Determine if this record is an edge.
            is_edge = (
                    "http://vital.ai/ontology/vital-core#hasEdgeSource" in record and
                    "http://vital.ai/ontology/vital-core#hasEdgeDestination" in record
            )
            if is_edge:
                for k in record.keys():
                    edge_keys.add(k)
            else:
                for k in record.keys():
                    node_keys.add(k)
    # Also include the additional reserved fields we are adding.
    node_keys.update(["~id", "~label"])
    edge_keys.update(["~id", "~from", "~to", "~label"])
    return sorted(node_keys), sorted(edge_keys)


def process_and_write_csv(node_fields, edge_fields):
    with open(NODES_OUTPUT, 'w', newline='', encoding='utf-8') as nodes_file, \
            open(EDGES_OUTPUT, 'w', newline='', encoding='utf-8') as edges_file, \
            open_input_file(INPUT_FILE) as infile:

        node_writer = csv.DictWriter(nodes_file, fieldnames=node_fields, extrasaction='ignore')
        edge_writer = csv.DictWriter(edges_file, fieldnames=edge_fields, extrasaction='ignore')

        node_writer.writeheader()
        edge_writer.writeheader()

        for line in infile:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Skipping invalid JSON line: {line}\nError: {e}", file=sys.stderr)
                continue

            is_edge = (
                    "http://vital.ai/ontology/vital-core#hasEdgeSource" in record and
                    "http://vital.ai/ontology/vital-core#hasEdgeDestination" in record
            )
            if is_edge:
                # Process record as an edge.
                edge = dict(record)  # Copy all properties from source.
                try:
                    edge["~id"] = record["URI"]
                except KeyError:
                    print("Edge record missing URI", file=sys.stderr)
                    continue
                edge["~from"] = record["http://vital.ai/ontology/vital-core#hasEdgeSource"]
                edge["~to"] = record["http://vital.ai/ontology/vital-core#hasEdgeDestination"]
                edge["~label"] = extract_label(record.get("type"))
                edge_writer.writerow(edge)
            else:
                # Process record as a node.
                node = dict(record)
                try:
                    node["~id"] = record["URI"]
                except KeyError:
                    print("Node record missing URI", file=sys.stderr)
                    continue
                node["~label"] = extract_label(record.get("type"))
                node_writer.writerow(node)


def main():
    print("Computing union of field keys (first pass)...")
    node_fields, edge_fields = compute_field_keys()
    print(f"Node fields: {node_fields}")
    print(f"Edge fields: {edge_fields}")
    print("Processing input file and writing CSV output (second pass)...")
    process_and_write_csv(node_fields, edge_fields)
    print(f"CSV files written: {NODES_OUTPUT}, {EDGES_OUTPUT}")


if __name__ == "__main__":
    main()
