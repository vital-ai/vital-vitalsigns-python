from typing import List
from vital_ai_vitalsigns.metaql.metaql_query import SelectQuery as MetaQLSelectQuery
from vital_ai_vitalsigns.metaql.metaql_query import GraphQuery as MetaQLGraphQuery
from vital_ai_vitalsigns.ontology.ontology import Ontology


class VirtuosoMetaQLImpl:

    @classmethod
    def generate_select_query_sparql(cls, *,
                                     select_query: MetaQLSelectQuery,
                                     namespace_list: List[Ontology]
                                     ) -> str:

        # print(select_query)

        graph_uri_list = select_query.get('graph_uri_list', [])

        graph_id_list = select_query.get('graph_id_list', [])


        print(graph_uri_list)

        print(graph_id_list)


        return ""


    @classmethod
    def generate_graph_query_sparql(cls, *,
                                    namespace: str = None,
                                    graph_query: MetaQLGraphQuery,
                                    namespace_list: List[Ontology]
                                    ) -> str:

        # print(graph_query)

        graph_uri_list = graph_query.get('graph_uri_list', [])

        graph_id_list = graph_query.get('graph_id_list', [])


        return ""


