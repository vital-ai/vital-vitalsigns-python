from vital_ai_vitalsigns.service.graph.graph_service import VitalGraphService


class VirtuosoGraphService(VitalGraphService):
    pass

"""
use this style for queries:
curl -X POST   -H "Content-Type: application/sparql-query" --digest -u "user:password" --data "SELECT DISTINCT ?g WHERE { GRAPH ?g {?s ?p ?o} } ORDER BY ?g"   http://localhost:8890/sparql-auth

use this style for crud operations:
except use rdf ntriples or nquads instead of turtle
probably n-triples since the graph uri is determined
application/n-triples
this would be for incremental updates rather than bulk
updates to multiple graphs would be split over N requests

curl -X PUT   -H "Content-Type: text/turtle"   --digest -u "user:password"   --data-binary @update.ttl   http://localhost:8890/sparql-graph-crud-auth?graph-uri=http://example.org/test3

"""
