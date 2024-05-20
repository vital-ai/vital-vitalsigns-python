from datetime import datetime
from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.URIReference import URIReference
from vital_ai_vitalsigns_core.model.VitalApp import VitalApp
from vital_ai_vitalsigns_core.model.VitalServiceSqlConfig import VitalServiceSqlConfig


def main():
    app = VitalApp()
    # app = VitalServiceSqlConfig()
    app.URI = 'urn:123'

    # print(app.URI)
    # print(app.name)

    app.name = "VitalApp"

    # app.username = "Fred"
    # person.birthday = datetime(1980, 1, 15)
    # person.nothing = "something"

    # print(app.name)

    # print(app.username)
    # print(person.birthday.get_uri())
    # print(person.nothing)

    json_string = app.to_json()

    # print(json_string)

    rdf_string = app.to_rdf()

    # print(rdf_string)

    node1 = VITAL_Node()
    node1.URI = "urn:node123"

    edge1 = VITAL_Edge()
    edge1.URI = "urn:edge123"

    edge1.edgeSource = "urn:node123"
    edge1.edgeDestination = "urn:node456"

    json_string = edge1.to_json()

    # print(json_string)

    rdf_string = edge1.to_rdf()

    # print(rdf_string)

    uri_ref = URIReference()

    uri_ref.URI = "urn:uriref123"

    uri_ref.uRIRef = node1.URI

    rdf_string = uri_ref.to_rdf()

    print(rdf_string)

    json_string = uri_ref.to_json()

    print(json_string)

    vs = VitalSigns()

    obj = vs.from_json(json_string)

    print(obj.to_rdf())

    obj = vs.from_rdf(rdf_string)

    print(obj.to_json())


if __name__ == "__main__":
    main()
