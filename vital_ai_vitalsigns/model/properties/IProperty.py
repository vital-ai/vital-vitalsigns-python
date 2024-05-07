from datetime import datetime
import rdflib


class IProperty:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def to_json(self):
        return {"value": self.value}

    def to_rdf(self):
        if isinstance(self.value, datetime):
            value = self.value.isoformat()
            datatype = rdflib.XSD.dateTime
        elif isinstance(self.value, int):
            value = str(self.value)
            datatype = rdflib.XSD.integer
        elif isinstance(self.value, float):
            value = str(self.value)
            datatype = rdflib.XSD.float
        elif isinstance(self.value, bool):
            value = str(self.value)
            datatype = rdflib.XSD.boolean
        else:
            value = str(self.value)
            datatype = rdflib.XSD.string
        return {"value": value, "datatype": datatype}
