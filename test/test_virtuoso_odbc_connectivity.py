import os
import pyodbc
import pytest

# You may want to move these to config or environment variables for real use
VIRTUOSO_DRIVER = os.environ.get(
    "VIRTUOSO_DRIVER",
    "/Library/ODBC/OpenLink Virtuoso ODBC Driver (Unicode).bundle/Contents/MacOS/virtodbcu_r.so"
)
VIRTUOSO_HOST = os.environ.get("VIRTUOSO_HOST", "localhost:1111")
VIRTUOSO_UID = os.environ.get("VIRTUOSO_UID", "dba")
VIRTUOSO_PWD = os.environ.get("VIRTUOSO_PWD", "dba")

def test_virtuoso_odbc_connectivity_only():
    """
    Test that we can connect to the Virtuoso ODBC instance (ODBC connectivity) and execute a simple SPARQL query.
    """
    connection_string = (
        f"DRIVER={VIRTUOSO_DRIVER};wideAsUTF16=Y;HOST={VIRTUOSO_HOST};UID={VIRTUOSO_UID};PWD={VIRTUOSO_PWD}"
    )
    try:
        connection = pyodbc.connect(connection_string, timeout=5)
        cursor = connection.cursor()
        res = cursor.execute("SPARQL SELECT DISTINCT ?g WHERE { GRAPH ?g {?s ?p ?o} } ORDER BY ?g")
        graphs = [row[0] for row in res]
        import logging
        logging.basicConfig(level=logging.INFO)
        logging.info(f"Found graph URIs: {graphs}")
        # If there's no data, that's still a valid connection
        assert cursor is not None
    except Exception as e:
        pytest.fail(f"Virtuoso ODBC connectivity test failed: {e}")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass
