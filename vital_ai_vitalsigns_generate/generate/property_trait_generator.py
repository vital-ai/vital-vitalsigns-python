

class VitalSignsPropertyTraitGenerator:

    @classmethod
    def generate_property_trait_string(cls,
                                       class_name: str,
                                       namespace: str,
                                       local_name: str,
                                       multiple_values: bool):

        # class_name = "Property_hasKGChatMessageText"
        # namespace = "http://vital.ai/ontology/haley-ai-kg#"
        # local_name = "hasKGChatMessageText"
        # multiple_values = False

        property_trait_string = f"""
from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait


class {class_name}(PropertyTrait):
    namespace = "{namespace}"
    local_name = "{local_name}"
    multiple_values = {multiple_values}

        """

        return property_trait_string


# sample

"""
from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait


class Property_hasKGChatMessageText(PropertyTrait):
    namespace = "http://vital.ai/ontology/haley-ai-kg#"
    local_name = "hasKGChatMessageText"
    multiple_values = False

"""
