
import datetime
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node


class VitalSegment(VITAL_Node):
        segmentGraphURI: str
        segmentID: str
        segmentNamespace: str
        segmentStateJSON: str
        segmentTenantID: str
        readOnly: bool
        segmentGlobal: bool

