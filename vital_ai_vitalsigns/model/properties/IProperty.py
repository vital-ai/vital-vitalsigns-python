from datetime import datetime
import rdflib


class IProperty:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def get_value(self):
        return self.value

    @classmethod
    def get_data_class(cls):
        return str

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
