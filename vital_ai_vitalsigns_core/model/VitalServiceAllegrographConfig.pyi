
import datetime
from vital_ai_vitalsigns_core.model.VitalServiceConfig import VitalServiceConfig


class VitalServiceAllegrographConfig(VitalServiceConfig):
        catalogName: str
        password: str
        poolMaxTotal: int
        repositoryName: str
        serverURL: str
        username: str

