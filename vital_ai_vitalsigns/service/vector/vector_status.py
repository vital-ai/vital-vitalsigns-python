from enum import Enum

class VitalVectorStatusType(Enum):
    OK = "VitalVectorStatusType_OK"
    ERROR = "VitalVectorStatusType_ERROR"

class VitalVectorStatus:
    status: VitalVectorStatusType = VitalVectorStatusType.OK
    status_message: str = ""

