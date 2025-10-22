from datetime import datetime
import rdflib

class IProperty:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    def get_value(self):
        return self.value

    @classmethod
    def get_data_class(cls):
        return str

    def to_json(self):
        return {"value": self.value}

    @classmethod
    def get_rdf_datatype(cls, value):
        if isinstance(value, datetime):
            datatype = rdflib.XSD.dateTime
        elif isinstance(value, bool):
            datatype = rdflib.XSD.boolean
        elif isinstance(value, int):
            datatype = rdflib.XSD.integer
        elif isinstance(value, float):
            datatype = rdflib.XSD.float
        else:
            datatype = rdflib.XSD.string
        return datatype

    def to_rdf(self):
        if isinstance(self.value, datetime):
            value = self.value.isoformat()
            datatype = rdflib.XSD.dateTime
        elif isinstance(self.value, bool):
            value = str(self.value)
            datatype = rdflib.XSD.boolean
        elif isinstance(self.value, int):
            value = str(self.value)
            datatype = rdflib.XSD.integer
        elif isinstance(self.value, float):
            value = str(self.value)
            datatype = rdflib.XSD.float
        else:
            value = str(self.value)
            datatype = rdflib.XSD.string
        return {"value": value, "datatype": datatype}
