import requests
import json

endpoint = "https://chat-saas-prod-db-neptune-1.cluster-czsnhy5vtw8f.us-east-1.neptune.amazonaws.com:8182/opencypher"


def get_property(entity, key):
    """
    Returns the property value for key from an entity (node or edge).
    Neptune typically nests properties under "~properties".
    """
    if isinstance(entity, dict):
        props = entity.get("~properties", entity)
        return props.get(key, "N/A")
    return "N/A"


def pretty_print_path(path_index, nodes, edges):
    print(f"Path {path_index}:")
    # Print first node
    n = nodes[0]
    uri = get_property(n, "URI")
    name = get_property(n, "vital.ai/ontology/vital-core_hasName")
    ntype = get_property(n, "type")
    print(f"  n1: URI: {uri}, Name: {name}, Type: {ntype}")

    # For each edge, print edge and subsequent node
    for i, edge in enumerate(edges, start=1):
        edge_uri = get_property(edge, "URI")
        edge_type = get_property(edge, "type")
        next_node = nodes[i]
        next_uri = get_property(next_node, "URI")
        next_name = get_property(next_node, "vital.ai/ontology/vital-core_hasName")
        next_type = get_property(next_node, "type")
        print(f"    --[e{i}: URI: {edge_uri}, Type: {edge_type}]->")
        print(f"       n{i + 1}: URI: {next_uri}, Name: {next_name}, Type: {next_type}")
    print()

# Multi-hop query:
# Matches a three-node path where nodes have the label NounSynsetNode
# and edges have the label Edge_WordnetHyponym.
# Returns the property "vital.ai/ontology/vital-core_hasName" from each node.
q1 = """
MATCH (a:NounSynsetNode)-[r:Edge_WordnetHyponym]->(b:NounSynsetNode)
MATCH (b)-[s:Edge_WordnetHyponym]->(c:NounSynsetNode)
RETURN a.`vital.ai/ontology/vital-core_hasName` AS nameA,
       b.`vital.ai/ontology/vital-core_hasName` AS nameB,
       c.`vital.ai/ontology/vital-core_hasName` AS nameC
LIMIT 10
"""

q2 = """
MATCH (a:NounSynsetNode)-[:Edge_WordnetHyponym]->(b:NounSynsetNode)-[:Edge_WordnetHyponym]->(c:NounSynsetNode)
RETURN count(*) AS totalPaths
"""

q3 = """
MATCH p=(a:NounSynsetNode)-[*2]->(b:NounSynsetNode)
WHERE toLower(a.`vital.ai/ontology/vital-core_hasName`) CONTAINS 'happy'
WITH nodes(p) AS ns, relationships(p) AS rs
RETURN ns, rs
LIMIT 100
"""

payload = {"query": q3}
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

try:
    response = requests.post(endpoint, json=payload, headers=headers, verify=False)
    response.raise_for_status()
    results = response.json()

    # Expect results["results"] to be a list of objects with keys "ns" and "rs"
    paths = results.get("results", [])
    if not paths:
        print("No paths found.")
    else:
        for idx, path in enumerate(paths, start=1):
            nodes = path.get("ns", [])
            edges = path.get("rs", [])
            if nodes:
                pretty_print_path(idx, nodes, edges)
            else:
                print(f"Path {idx}: No nodes returned.")
except requests.exceptions.RequestException as e:
    print("Error querying Neptune openCypher endpoint:", e)

"""
try:
    response = requests.post(endpoint, json=payload, headers=headers, verify=False)
    response.raise_for_status()
    results = response.json()
    print(json.dumps(results, indent=2))
except requests.exceptions.RequestException as e:
    print("Error querying Neptune openCypher endpoint:", e)
"""