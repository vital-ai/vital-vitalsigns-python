import requests
import json
import time

# Neptune SPARQL endpoint URL (update with your actual endpoint)
endpoint = "https://chat-saas-prod-db-neptune-1.cluster-czsnhy5vtw8f.us-east-1.neptune.amazonaws.com:8182/sparql"

def get_subjects(limit=10000):
    # Retrieve a batch of subjects from the default graph
    query = f"""
    SELECT ?s
    WHERE {{
      ?s ?p ?o .
    }}
    LIMIT {limit}
    """
    headers = {
        "Content-Type": "application/sparql-query",
        "Accept": "application/sparql-results+json"
    }
    response = requests.post(endpoint, data=query, headers=headers, verify=False)
    response.raise_for_status()
    results = response.json()
    subjects = [binding["s"]["value"] for binding in results["results"]["bindings"]]
    return subjects

def delete_subjects(subjects):
    # Create a VALUES clause with the batch of subjects
    values_clause = "VALUES ?s { " + " ".join(f"<{s}>" for s in subjects) + " }"
    update_query = f"""
    DELETE {{
      ?s ?p ?o .
    }}
    WHERE {{
      {values_clause}
      ?s ?p ?o .
    }}
    """
    headers = {"Content-Type": "application/sparql-update"}
    response = requests.post(endpoint, data=update_query, headers=headers, verify=False)
    response.raise_for_status()
    return response.text

# Loop: delete triples in batches until the default graph is empty.
while True:
    subjects = get_subjects(limit=100000)
    if not subjects:
        print("No more triples to delete in the default graph.")
        break
    print(f"Deleting triples for {len(subjects)} subjects...")
    result = delete_subjects(subjects)
    print(result)
    # Sleep briefly to give the cluster time to process
    time.sleep(0.1)
