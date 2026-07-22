
class DomainOntologyClassGenerator:

    def __init__(self):
        pass

    @classmethod
    def generate(cls, ont_iri: str):

        # Byte-for-byte format of the committed 6-line DomainOntology.py:
        # leading blank line, import, two blank lines, class line,
        # OntologyURI line, single trailing newline.
        domain_ontology_class = (
            "\n"
            "from vital_ai_vitalsigns.model.BaseDomainOntology import BaseDomainOntology\n"
            "\n"
            "\n"
            "class DomainOntology(BaseDomainOntology):\n"
            f'    OntologyURI = "{ont_iri}"\n'
        )

        return domain_ontology_class


# sample:
"""
from vital_ai_vitalsigns.model.BaseDomainOntology import BaseDomainOntology


class DomainOntology(BaseDomainOntology):
    OntologyURI = "http://vital.ai/ontology/vital-aimp" 
"""