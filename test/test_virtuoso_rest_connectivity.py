import os
import requests
import pytest

VIRTUOSO_REST_ENDPOINT = os.environ.get("VIRTUOSO_REST_ENDPOINT", "http://localhost:8890/sparql")
VIRTUOSO_UID = os.environ.get("VIRTUOSO_UID", "dba")
VIRTUOSO_PWD = os.environ.get("VIRTUOSO_PWD", "dba")

def test_virtuoso_rest_connectivity_only():
    """
    Test that we can connect to the Virtuoso REST endpoint and execute a simple SPARQL query.
    """
    query = "SELECT DISTINCT ?g WHERE { GRAPH ?g {?s ?p ?o} } ORDER BY ?g"
    params = {
        'query': query,
        'format': 'application/sparql-results+json',
    }
    try:
        response = requests.get(
            VIRTUOSO_REST_ENDPOINT,
            params=params,
            auth=(VIRTUOSO_UID, VIRTUOSO_PWD),
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        graphs = [binding['g']['value'] for binding in data.get('results', {}).get('bindings', [])]
        import logging
        logging.basicConfig(level=logging.INFO)
        logging.info(f"Found graph URIs (REST): {graphs}")
        assert isinstance(graphs, list)
    except Exception as e:
        pytest.fail(f"Virtuoso REST connectivity test failed: {e}")
