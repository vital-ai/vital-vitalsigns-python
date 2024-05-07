from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty


def main():
    combined_instance = VitalSignsImpl.create_property_with_trait(
        StringProperty,
        "http://vital.ai/ontology/vital-core#hasName",
        "John")
    print(f"Value: {combined_instance.value}")
    print(f"URI: {combined_instance.get_uri()}")
    print(f"URI: {combined_instance.get_short_name()}")


if __name__ == "__main__":
    main()
