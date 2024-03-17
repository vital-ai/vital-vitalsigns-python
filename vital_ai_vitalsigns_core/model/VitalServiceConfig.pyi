
import datetime
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node


class VitalServiceConfig(VITAL_Node):
        appID: str
        configString: str
        connectionError: str
        connectionState: str
        defaultSegmentName: str
        key: str
        organizationID: str
        targetAppID: str
        targetOrganizationID: str
        uriGenerationStrategy: str
        primary: bool

