import json
from ai_haley_kg_domain.model.KGEntity import KGEntity
from vital_ai_vitalsigns.metaql.metaql_parser import MetaQLParser
from vital_ai_vitalsigns.metaql.query.query_builder import QueryBuilder, AndConstraintList, ConstraintType, \
    ClassConstraint, VectorConstraint
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.properties.Property_hasName import Property_hasName


def main():
    print('Test MetaQL Select Vector Builder')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    wordnet_graph_uri = 'http://vital.ai/graph/wordnet-frames-graph-1'

    wordnet_graph_id = 'wordnet-frames-graph-1'

    sq = (
        QueryBuilder.select_query(
            limit=10, offset=0
        )
        .graph_uri(wordnet_graph_id)
        .constraint_list(
            AndConstraintList()
            .node_constraint(
                VectorConstraint(
                    vector_name="value",
                    vector_value="happy"
                )
            )
            .node_constraint(
                VectorConstraint(
                    vector_name="type",
                    vector_value="person"
                )
            )
            .node_constraint(
                ClassConstraint(
                    clazz=KGEntity.get_class_uri()
                )
            )
        )
        .build()
    )

    print(sq)

    select_query_json = json.dumps(sq, indent=4)

    print(select_query_json)

    metaql_query_dict = json.loads(select_query_json)

    metaql_query = MetaQLParser.parse_metaql_dict(metaql_query_dict)

    print(metaql_query)



if __name__ == "__main__":
    main()

