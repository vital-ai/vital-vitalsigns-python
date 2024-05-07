from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.query.vital_graph_query import VitalGraphQuery, Arc, ref, ArcAnd, bind
from vital_ai_vitalsigns.query.vital_select_query import VitalSelectQuery
from vital_ai_vitalsigns_core.model.properties.Property_URIProp import Property_URIProp


def main():
    print('Hello World')

    # MetaQL Select Query
    """
    SELECT {
        value limit: 100
        value offset: 0
        value segments: ["mydata"]
        constraint { Person.class }
        constraint { Person.props().name.equalTo("John" ) }
    }
    """

    select_query = (VitalSelectQuery()
                    .add_segment("mydata")
                    .node_constraint(VITAL_Node)
                    .edge_constraint(VITAL_Edge)
                    .node_constraint(VITAL_Node.name == "John")
                    )

    print(select_query)

    # MetaQL: Graph Query
    """
    GRAPH {
        value segments: ["mydata"]
        ARC {
          node_constraint { Email.class }
          constraint { "?person1 != ?person2" }
          ARC_AND {
              ARC {
                edge_constraint { Edge_hasSender.class }
                node_constraint { Person.props().emailAddress.equalTo("john@example.org")
                node_constraint { Person.class }
                node_provides { "person1 = URI" }
             }
              ARC {
                edge_constraint { Edge_hasRecipient.class }
                node_constraint { Person.class }
                node_provides { "person2 = URI" }
             }
          }
        }
    }
    """

    graph_query = (VitalGraphQuery()
                   .add_segment("mydata")
                   .add_arc(Arc()
                            .node_constraint(VITAL_Node)
                            .constraint(ref("person1") != ref("person2"))
                            .add_arc(ArcAnd()
                                     .add_arc(Arc()
                                        .edge_constraint(VITAL_Edge)
                                        .node_constraint(VITAL_Node.name == "John")
                                        .node_constraint(VITAL_Node)
                                        .provides(bind("person1").to(Property_URIProp)))
                                     .add_arc(Arc()
                                        .edge_constraint(VITAL_Edge)
                                        .node_constraint(VITAL_Node)
                                        .provides(bind("person2").to(Property_URIProp)))
                                     )
                            )
                   )

    print(graph_query)

    # sparql = graph.to_sparql()
    # print(sparql)


if __name__ == "__main__":
    main()
