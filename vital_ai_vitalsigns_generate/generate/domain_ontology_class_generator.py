
class DomainOntologyClassGenerator:

    def __init__(self):
        pass

    @classmethod
    def generate(cls, ont_iri: str):

        domain_ontology_class = f"""
from vital_ai_vitalsigns.model.BaseDomainOntology import BaseDomainOntology


class DomainOntology(BaseDomainOntology):
    OntologyURI = "{ont_iri}"
 
        """

        return domain_ontology_class


# sample:
"""
from vital_ai_vitalsigns.model.BaseDomainOntology import BaseDomainOntology


class DomainOntology(BaseDomainOntology):
    OntologyURI = "http://vital.ai/ontology/vital-aimp" 
"""