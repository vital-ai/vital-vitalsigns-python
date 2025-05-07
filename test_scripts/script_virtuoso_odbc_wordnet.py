import pyodbc
import time


def main():
    print('Test Virtuoso ODBC Connection')

    endpoint = "localhost"
    user = "dba"
    password = "dba"

    connection = pyodbc.connect(f'DRIVER=/Library/ODBC/OpenLink Virtuoso ODBC Driver (Unicode).bundle/Contents/MacOS/virtodbcu_r.so;wideAsUTF16=Y;HOST={endpoint};UID={user};PWD={password}')

    # cursor = connection.cursor()

    query = f"""
            PREFIX vital: <http://vital.ai/ontology/vital-core#>

SELECT ?connectedNode ?predicate ?object
WHERE {{
    GRAPH <http://vital.ai/graph/wordnet-graph-1> {{
        # Subquery to find unique connected nodes
        {{
            SELECT DISTINCT ?connectedNode
            WHERE {{
                ?happyNode vital:hasName ?name .
                FILTER(CONTAINS(LCASE(STR(?name)), "happy"))

                {{
                    ?edge vital:hasEdgeSource ?happyNode .
                    ?edge vital:hasEdgeDestination ?connectedNode .
                }} UNION {{
                    ?edge vital:hasEdgeDestination ?happyNode .
                    ?edge vital:hasEdgeSource ?connectedNode .
                }}
            }}
        }}

        # Get all triples of the unique connected nodes
        ?connectedNode ?predicate ?object .
    }}
}}
ORDER BY ?connectedNode
            """

    # res = cursor.execute("SPARQL SELECT DISTINCT ?g WHERE { GRAPH ?g {?s ?p ?o} } ORDER BY ?g")

    start_time = time.time()

    cursor = connection.cursor()

    res = cursor.execute(f"SPARQL {query}")

    res = cursor.execute(f"SPARQL {query}")

    res = cursor.execute(f"SPARQL {query}")

    res = cursor.execute(f"SPARQL {query}")

    res = cursor.execute(f"SPARQL {query}")

    res = cursor.execute(f"SPARQL {query}")

    res = cursor.execute(f"SPARQL {query}")

    res = cursor.execute(f"SPARQL {query}")

    res = cursor.execute(f"SPARQL {query}")

    res = cursor.execute(f"SPARQL {query}")

    end_time = time.time()
    time_difference_ms = (end_time - start_time) * 1000
    print(f"The function took {round(time_difference_ms)} ms.")

    # print(res.rowcount)

    # needed to commit changes.
    # will be good for rolling back transactions.

    # connection.commit()

    # print(res)

    for r in res:
        # print(r)
        pass

    # res.next()


if __name__ == "__main__":
    main()
