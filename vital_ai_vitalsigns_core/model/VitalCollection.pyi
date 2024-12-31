
import datetime
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node


class VitalCollection(VITAL_Node):
        collectionClassName: str
        collectionClassURI: str
        collectionID: str
        collectionNamespace: str
        collectionSchemaName: str
        collectionSchemaType: str
        collectionSchemaVersion: str
        collectionSchemaYAML: str
        collectionMultiTenant: bool
        includesSubclasses: bool

