
import datetime
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node


class AggregationResult(VITAL_Node):
        aggregationType: str
        value: float

