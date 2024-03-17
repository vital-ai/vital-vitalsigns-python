
import datetime
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node


class DomainModel(VITAL_Node):
        appID: str
        backwardCompVersion: str
        defaultPackageValue: str
        domainOWL: str
        domainOWLHash: str
        organizationID: str
        preferredImportVersions: str
        versionInfo: str
        preferred: bool

