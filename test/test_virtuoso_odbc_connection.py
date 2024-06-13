from utils.config_utils import ConfigUtils
import pyodbc


def main():
    print('Test Virtuoso ODBC Connection')

    config = ConfigUtils.load_config()

    connection = pyodbc.connect('DRIVER=/Library/ODBC/OpenLink Virtuoso ODBC Driver (Unicode).bundle/Contents/MacOS/virtodbcu_r.so;wideAsUTF16=Y;HOST=localhost:1111;UID=dba;PWD=dba')

    cursor = connection.cursor()

    insert = f"""
            INSERT DATA {{
                GRAPH <http://vital.ai/graph/kgframe-test-1> {{
                    <urn:test123> <rdf:type> <urn:testtype> .
                }}
            }}
            """

    res = cursor.execute("SPARQL SELECT DISTINCT ?g WHERE { GRAPH ?g {?s ?p ?o} } ORDER BY ?g")

    # res = cursor.execute(f"SPARQL {insert}")

    # print(res.rowcount)

    # needed to commit changes.
    # will be good for rolling back transactions.

    # connection.commit()

    print(res)

    for r in res:
        print(r)

    # res.next()


if __name__ == "__main__":
    main()
