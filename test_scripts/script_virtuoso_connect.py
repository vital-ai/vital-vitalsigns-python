from SPARQLWrapper import SPARQLWrapper, JSON


def main():
    print('Hello World')
    # local install of open source virtuoso with
    # sparql endpoint enabled without authentication
    server_name = 'localhost'
    server_port = 8890
    sparql = SPARQLWrapper("http://localhost:8890/sparql")
    sparql.setQuery("""
        SELECT  DISTINCT ?g 
            WHERE  { GRAPH ?g {?s ?p ?o} } 
            ORDER BY  ?g
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        print(result["g"]["value"])


if __name__ == "__main__":
    main()


