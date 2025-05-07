from vital_ai_vitalsigns.vitalsigns import VitalSigns


def main():
    print('Weaviate Wordnet Import with Schema')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    # default case is not to create a collection for Edges
    # edge information is available in the graph database
    # and object / cross-ref / object use edge name property
    # so edges can be found with sourceURI, destinationURI, and edge class
    # there could be ambiguity via namespace
    # but that could be encoded into the property name if needed

    # wordnet data is in graph database
    # define schema to use for collection and
    # trigger indexing of the collection

    # schema allows multiple vectors and mapping from property to vector

    # note: currently can only search one vector at a time
    # asked in slack about combining queries over multiple vectors

    synset_node_schema = {
        "collection_name": "SynsetNode",
        "collapse_class_hierarchy": True,
        "vectors": {
            {"name": "synsetnode_vector"},
            # {"name": "synsetnode_vector_type"}
        },
        "properties": {
            # URI property always present
            "URI": {"name": "uri", "data_type": "uri"},
            # special property for class URI
            "type": {"name": "subclassURI", "data_type": "class_uri"},
            "hasName": {"name": "hasName", "data_type": "text", "vectorize": True, "vector": "synsetnode_vector"},
            "hasGloss": {"name": "hasGloss", "data_type": "text", "vectorize": True, "vector": "synsetnode_vector"},
            "hasWordnetID": {"name": "hasWordnetID", "data_type": "text", "vectorize": False}
        },
        "references": {
            "Edge_WordnetAlsoSee": {"name": "edge_WordnetAlsoSee", "targetCollection": "SynsetNode"},
            "Edge_WordnetAntonym": {"name": "edge_WordnetAntonym", "targetCollection": "SynsetNode"},
            "Edge_WordnetAttribute": {"name": "edge_WordnetAttribute", "targetCollection": "SynsetNode"},
            "Edge_WordnetCause": {"name": "edge_WordnetCause", "targetCollection": "SynsetNode"},
            "Edge_WordnetDerivationallyRelatedForm": {"name": "edge_WordnetDerivationallyRelatedForm", "targetCollection": "SynsetNode"},
            "Edge_WordnetDerivedFromAdjective": {"name": "edge_WordnetDerivedFromAdjective", "targetCollection": "SynsetNode"},
            "Edge_WordnetDomainOfSynset_Region": {"name": "edge_WordnetDomainOfSynset_Region", "targetCollection": "SynsetNode"},
            "Edge_WordnetDomainOfSynset_Topic": {"name": "edge_WordnetDomainOfSynset_Topic", "targetCollection": "SynsetNode"},
            "Edge_WordnetDomainOfSynset_Usage": {"name": "edge_WordnetDomainOfSynset_Usage", "targetCollection": "SynsetNode"},
            "Edge_WordnetEntailment": {"name": "edge_WordnetEntailment", "targetCollection": "SynsetNode"},
            "Edge_WordnetHypernym": {"name": "edge_WordnetHypernym", "targetCollection": "SynsetNode"},
            "Edge_WordnetHyponym": {"name": "edge_WordnetHyponym", "targetCollection": "SynsetNode"},
            "Edge_WordnetInstanceHypernym": {"name": "edge_WordnetInstanceHypernym", "targetCollection": "SynsetNode"},
            "Edge_WordnetInstanceHyponym": {"name": "edge_WordnetInstanceHyponym", "targetCollection": "SynsetNode"},
            "Edge_WordnetMemberHolonym": {"name": "edge_WordnetMemberHolonym", "targetCollection": "SynsetNode"},
            "Edge_WordnetMemberMeronym": {"name": "edge_WordnetMemberMeronym", "targetCollection": "SynsetNode"},
            "Edge_WordnetMemberOfThisDomain_Region": {"name": "edge_WordnetMemberOfThisDomain_Region", "targetCollection": "SynsetNode"},
            "Edge_WordnetMemberOfThisDomain_Topic": {"name": "edge_WordnetMemberOfThisDomain_Topic", "targetCollection": "SynsetNode"},
            "Edge_WordnetMemberOfThisDomain_Usage": {"name": "edge_WordnetMemberOfThisDomain_Usage", "targetCollection": "SynsetNode"},
            "Edge_WordnetPartHolonym": {"name": "edge_WordnetPartHolonym", "targetCollection": "SynsetNode"},
            "Edge_WordnetParticiple": {"name": "edge_WordnetParticiple", "targetCollection": "SynsetNode"},
            "Edge_WordnetPartMeronym": {"name": "edge_WordnetPartMeronym", "targetCollection": "SynsetNode"},
            "Edge_WordnetPertainym_PertainsToNouns": {"name": "edge_WordnetPertainym_PertainsToNouns", "targetCollection": "SynsetNode"},
            "Edge_WordnetSimilarTo": {"name": "edge_WordnetSimilarTo", "targetCollection": "SynsetNode"},
            "Edge_WordnetSubstanceHolonym": {"name": "edge_WordnetSubstanceHolonym", "targetCollection": "SynsetNode"},
            "Edge_WordnetSubstanceMeronym": {"name": "edge_WordnetSubstanceMeronym", "targetCollection": "SynsetNode"},
            "Edge_WordnetVerbGroup": {"name": "edge_WordnetVerbGroup", "targetCollection": "SynsetNode"}
        }
    }


if __name__ == "__main__":
    main()

