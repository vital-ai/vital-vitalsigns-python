import rdflib
from rdflib import URIRef
from vital_ai_vitalsigns.model.properties.IProperty import IProperty


class URIProperty(IProperty):
    def __init__(self, value: str):
        str_value = str(value)
        super().__init__(str_value)

    def __bool__(self):
        return bool(self.value)

    def __getattr__(self, attr):
        return getattr(self.value, attr)

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        elif isinstance(other, URIProperty):
            return self.value == other.value
        return NotImplemented

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        value = str(self.value)
        return {"value": value}

    def to_rdf(self):
        datatype = URIRef
        value = str(self.value)
        return {"value": value, "datatype": datatype}


