
import datetime
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node


class RDFStatement(VITAL_Node):
        rdfContext: str
        rdfObject: str
        rdfPredicate: str
        rdfSubject: str

