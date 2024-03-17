
import datetime
from vital_ai_vitalsigns_core.model.VitalServiceConfig import VitalServiceConfig


class VitalServiceSqlConfig(VitalServiceConfig):
        dbType: str
        endpointURL: str
        password: str
        poolInitialSize: int
        poolMaxTotal: int
        username: str

