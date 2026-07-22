

# Fixed block of 11 property-class imports, emitted unconditionally to match
# the committed Groovy output (PythonDomainGenerator.groovy).
property_import_string = """from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
from vital_ai_vitalsigns.model.properties.DateTimeProperty import DateTimeProperty
from vital_ai_vitalsigns.model.properties.DoubleProperty import DoubleProperty
from vital_ai_vitalsigns.model.properties.FloatProperty import FloatProperty
from vital_ai_vitalsigns.model.properties.GeoLocationProperty import GeoLocationProperty
from vital_ai_vitalsigns.model.properties.IntegerProperty import IntegerProperty
from vital_ai_vitalsigns.model.properties.LongProperty import LongProperty
from vital_ai_vitalsigns.model.properties.OtherProperty import OtherProperty
from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
from vital_ai_vitalsigns.model.properties.TruthProperty import TruthProperty
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
"""


class VitalSignsClassGenerator:

    @classmethod
    def generate_class_string(cls,
                              parent_class_import: str,
                              parent_class_name: str,
                              class_name: str,
                              class_uri: str,
                              property_list: list[dict]):

        property_list_string = cls.generate_property_list_string(property_list)

        # Byte-for-byte format of the committed Groovy-generated class files:
        # leading blank line, 11 property imports, parent import (no blank
        # between), two blank lines, class body, trailing blank line.
        class_string = (
            "\n"
            f"{property_import_string}"
            f"from {parent_class_import} import {parent_class_name}\n"
            "\n"
            "\n"
            f"class {class_name}({parent_class_name}):\n"
            "    _allowed_properties = [\n"
            f"{property_list_string}"
            "    ]\n"
            "\n"
            "    @classmethod\n"
            "    def get_allowed_properties(cls):\n"
            f"        return super().get_allowed_properties() + {class_name}._allowed_properties\n"
            "\n"
            "    @classmethod\n"
            "    def get_class_uri(cls) -> str:\n"
            f"        return '{class_uri}'\n"
            "\n"
        )

        return class_string

    # property_list = [
    #    {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentAvatarImageSourceURL', 'prop_class': 'StringProperty'},
    # ]

    @classmethod
    def generate_property_list_string(cls, property_list: list[dict]):

        # Each entry: 8-space indent, terminated by "}, " (comma + one
        # trailing space) including the last entry — matches committed output.
        property_list_string = "".join(
            f"        {{'uri': '{entry['uri']}', 'prop_class': {entry['prop_class']}}}, \n"
            for entry in property_list
        )

        return property_list_string

    @classmethod
    def generate_class_interface_string(
            cls,
            parent_class_import: str,
            parent_class_name: str,
            class_name: str,
            property_interface_list: list[dict]):

        if len(property_interface_list) > 0:
            # Property lines followed by a trailing blank line (committed form).
            property_interface_list_string = cls.generate_property_list_interface_string(property_interface_list) + "\n"
        else:
            # Empty class body: single "    pass" line, no trailing blank line.
            property_interface_list_string = "    pass\n"

        class_interface_string = (
            "\n"
            "import datetime\n"
            f"from {parent_class_import} import {parent_class_name}\n"
            "\n"
            "\n"
            f"class {class_name}({parent_class_name}):\n"
            f"{property_interface_list_string}"
        )

        return class_interface_string

    # properties = [
    #    {'short_prop_name': 'kGAgentAvatarImageSourceURL', 'datatype': 'str'},
    # ]

    @classmethod
    def generate_property_list_interface_string(cls, property_interface_list: list[dict]):

        # 8-space indent per property line — matches committed output.
        property_interface_list_string = "".join(
            f"        {entry['short_prop_name']}: {entry['datatype']}\n"
            for entry in property_interface_list
        )

        return property_interface_list_string

# sample class
"""

from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
from vital_ai_vitalsigns.model.properties.DateTimeProperty import DateTimeProperty
from vital_ai_vitalsigns.model.properties.DoubleProperty import DoubleProperty
from vital_ai_vitalsigns.model.properties.FloatProperty import FloatProperty
from vital_ai_vitalsigns.model.properties.GeoLocationProperty import GeoLocationProperty
from vital_ai_vitalsigns.model.properties.IntegerProperty import IntegerProperty
from vital_ai_vitalsigns.model.properties.LongProperty import LongProperty
from vital_ai_vitalsigns.model.properties.OtherProperty import OtherProperty
from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
from vital_ai_vitalsigns.model.properties.TruthProperty import TruthProperty
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
from ai_haley_kg_domain.model.KGNode import KGNode


class KGAgent(KGNode):
    _allowed_properties = [
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentAvatarImageSourceURL', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentAvatarImageURL', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentAvatarLargeImageURL', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentDeploymentURL', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentDescription', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentIdentifier', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentImplIdentifier', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentModificationDateTime', 'prop_class': DateTimeProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentName', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentNameSlug', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentPublishStatusURI', 'prop_class': URIProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentPublisherName', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentRankingScore', 'prop_class': DoubleProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentRankingScoreUpdateDateTime', 'prop_class': DateTimeProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentServiceURIs', 'prop_class': URIProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGAgentType', 'prop_class': URIProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasKGBracketURIs', 'prop_class': URIProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasPrimaryLanguageType', 'prop_class': URIProperty}, 
        {'uri': 'http://vital.ai/ontology/haley-ai-kg#hasTopCategoryURIs', 'prop_class': URIProperty}, 
    ]

    @classmethod
    def get_allowed_properties(cls):
        return super().get_allowed_properties() + KGAgent._allowed_properties

    @classmethod
    def get_class_uri(cls) -> str:
        return 'http://vital.ai/ontology/haley-ai-kg#KGAgent'

"""

# sample pyi

"""
import datetime
from ai_haley_kg_domain.model.KGNode import KGNode


class KGAgent(KGNode):
        kGAgentAvatarImageSourceURL: str
        kGAgentAvatarImageURL: str
        kGAgentAvatarLargeImageURL: str
        kGAgentDeploymentURL: str
        kGAgentDescription: str
        kGAgentIdentifier: str
        kGAgentImplIdentifier: str
        kGAgentModificationDateTime: datetime
        kGAgentName: str
        kGAgentNameSlug: str
        kGAgentPublishStatusURI: str
        kGAgentPublisherName: str
        kGAgentRankingScore: float
        kGAgentRankingScoreUpdateDateTime: datetime
        kGAgentServiceURIs: str
        kGAgentType: str
        kGBracketURIs: str
        primaryLanguageType: str
        topCategoryURIs: str
        
"""


