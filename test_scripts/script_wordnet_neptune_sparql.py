import requests
import json

endpoint = "https://chat-saas-prod-db-neptune-1.cluster-czsnhy5vtw8f.us-east-1.neptune.amazonaws.com:8182/sparql"

query_orig = """
PREFIX vital-core: <http://vital.ai/ontology/vital-core#>
PREFIX vital: <http://vital.ai/ontology/vital#>
PREFIX vital-aimp: <http://vital.ai/ontology/vital-aimp#>
PREFIX haley: <http://vital.ai/ontology/haley>
PREFIX haley-ai-question: <http://vital.ai/ontology/haley-ai-question#>
PREFIX haley-ai-kg: <http://vital.ai/ontology/haley-ai-kg#>

CONSTRUCT {
  _:bnode1 <urn:hasEntity> ?entity .
  _:bnode1 <urn:hasFrame> ?frame .
  _:bnode1 <urn:hasSourceSlot> ?sourceSlot .
  _:bnode1 <urn:hasDestinationSlot> ?destinationSlot .
  _:bnode1 <urn:hasSourceSlotEntity> ?sourceSlotEntity .
  _:bnode1 <urn:hasDestinationSlotEntity> ?destinationSlotEntity .
}
WHERE {
  SELECT ?entity ?frame ?sourceSlot ?destinationSlot ?sourceSlotEntity ?destinationSlotEntity WHERE {
    {
      ?sourceSlotEntity a haley-ai-kg:KGEntity .
      ?sourceSlotEntity haley-ai-kg:hasKGraphDescription ?description1 .
      FILTER(CONTAINS(LCASE(STR(?description1)), "happy"))
      BIND(?sourceSlotEntity AS ?entity)
    }
    UNION
    {
      ?destinationSlotEntity a haley-ai-kg:KGEntity .
      ?destinationSlotEntity haley-ai-kg:hasKGraphDescription ?description2 .
      FILTER(CONTAINS(LCASE(STR(?description2)), "happy"))
      BIND(?destinationSlotEntity AS ?entity)
    }
    ?frame a haley-ai-kg:KGFrame .
    
    ?sourceEdge a haley-ai-kg:Edge_hasKGSlot .
    ?sourceEdge vital-core:hasEdgeSource ?frame .
    ?sourceEdge vital-core:hasEdgeDestination ?sourceSlot .
    ?sourceSlot a haley-ai-kg:KGEntitySlot .
    ?sourceSlot haley-ai-kg:hasEntitySlotValue ?sourceSlotEntity .
    ?sourceSlot haley-ai-kg:hasKGSlotType <urn:hasSourceEntity> .
    
    ?destinationEdge a haley-ai-kg:Edge_hasKGSlot .
    ?destinationEdge vital-core:hasEdgeSource ?frame .
    ?destinationEdge vital-core:hasEdgeDestination ?destinationSlot .
    ?destinationSlot a haley-ai-kg:KGEntitySlot .
    ?destinationSlot haley-ai-kg:hasEntitySlotValue ?destinationSlotEntity .
    ?destinationSlot haley-ai-kg:hasKGSlotType <urn:hasDestinationEntity> .
  }
}
ORDER BY ?entity
LIMIT 10
OFFSET 0

"""

# Headers to indicate SPARQL query format and request JSON output
headers = {
    "Content-Type": "application/sparql-query",
    "Accept": "application/sparql-results+json"
}

try:
    response = requests.post(endpoint, data=query_orig, headers=headers, verify=False)
    response.raise_for_status()
    results = response.json()
    print(json.dumps(results, indent=2))
except requests.exceptions.RequestException as e:
    print("Error querying Neptune SPARQL endpoint:", e)
