from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.GraphMatch import GraphMatch
from vital_ai_vitalsigns_core.model.VitalApp import VitalApp


def main():

    print("Test GraphMatch/GCO")

    vs = VitalSigns()

    print("Initialized...")

    app = VitalApp()

    gm = GraphMatch()

    gm.URI = "urn:123"

    gm.something = 12

    # print(gm._extern_properties)

    for name, prop in gm._extern_properties.items():
        print(f"{name}:{prop}")

    print(gm.something)

    print(gm.to_json())

    print(gm.to_rdf())

    json = gm.to_json()

    triples = gm.to_rdf()

    obj = vs.from_json(json)

    print(obj.to_rdf())

    obj = vs.from_rdf(triples)

    print(obj.to_json())

    gm.frame = "urn:456"
    gm.slotEdge = "urn:789"
    gm.slot = "urn:321"

    frame_node = VITAL_Node()
    frame_node.URI = "urn:456"
    frame_node.name = "Frame"

    slot_edge = VITAL_Edge()
    slot_edge.URI = "urn:789"

    slot = VITAL_Node()
    slot.URI = "urn:321"

    # can use:
    # gm.set_property(name, value)
    # gm.get_property(name)
    # when name is a URI or a dynamic string
    # versus a property ame used directly in code like:
    # gm.something = value
    # this is in place of groovy which allows gm."hello"

    # adding map key style access to attributes

    # so obj.name is the same as obj["name"]
    # which is convenient for dynamic keys like setting/getting
    # dynamic properties for graphmatch URI values

    gm.set_property(frame_node.URI, frame_node.to_json())

    print(gm.to_json())

    # obj = gm.get_property(frame_node.URI)

    # print(obj.name)

    # print(obj.to_rdf())

    obj = gm[frame_node.URI]

    print(obj.name)

    print(obj.to_rdf())

    print(obj["name"])

    gm.name = "GraphMatch"

    print(gm.keys())

    print(gm.values())

    for v in gm.values():
        print(v.get_value())

    for k, v in gm.items():
        print(f"Key: {k} : Value: {v}")

    print(gm.to_rdf())


if __name__ == "__main__":
    main()


