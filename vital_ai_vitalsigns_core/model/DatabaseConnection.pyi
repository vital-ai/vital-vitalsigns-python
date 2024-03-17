
import datetime
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node


class DatabaseConnection(VITAL_Node):
        appID: str
        configString: str
        endpointType: str
        endpointURL: str
        organizationID: str
        password: str
        username: str
        readOnly: bool

