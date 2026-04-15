from datetime import datetime
import rdflib
from rdflib import URIRef

_DATACLASS_TO_XSD = {
    datetime: rdflib.XSD.dateTime,
    int: rdflib.XSD.integer,
    float: rdflib.XSD.float,
    bool: rdflib.XSD.boolean,
}


def get_xsd_datatype(data_class):
    return _DATACLASS_TO_XSD.get(data_class, rdflib.XSD.string)
