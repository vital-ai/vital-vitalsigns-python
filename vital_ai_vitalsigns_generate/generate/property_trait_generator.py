

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

        # Byte-for-byte format of committed trait files: import line at top
        # (no leading blank line), two blank lines, class + 3 attribute lines,
        # single trailing newline.
        property_trait_string = (
            "from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait\n"
            "\n"
            "\n"
            f"class {class_name}(PropertyTrait):\n"
            f'    namespace = "{namespace}"\n'
            f'    local_name = "{local_name}"\n'
            f"    multiple_values = {multiple_values}\n"
        )

        return property_trait_string


# sample

"""
from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait


class Property_hasKGChatMessageText(PropertyTrait):
    namespace = "http://vital.ai/ontology/haley-ai-kg#"
    local_name = "hasKGChatMessageText"
    multiple_values = False

"""
