from __future__ import annotations

from typing import Type, Any, Dict, Optional, List, Union, TypeVar
from datetime import datetime
from functools import lru_cache

# Pydantic v2 imports (required)
try:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import core_schema
    PYDANTIC_V2_AVAILABLE = True
except ImportError:
    PYDANTIC_V2_AVAILABLE = False
    GetCoreSchemaHandler = None
    core_schema = None

G = TypeVar('G', bound=Optional['GraphObject'])


class GraphObjectPydanticUtils:
    """Utility class containing Pydantic v2 functionality for GraphObject."""

    @staticmethod
    def get_pydantic_core_schema_impl(
        cls, 
        source_type: Type[Any], 
        handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic v2 core schema generation for GraphObject classes."""
        if not PYDANTIC_V2_AVAILABLE:
            raise ImportError("Pydantic v2 is required for this functionality")
            
        from pydantic_core import core_schema
        
        # Create a schema that treats GraphObject as an opaque object
        # This avoids Pydantic trying to introspect VitalSigns internals
        return core_schema.with_info_plain_validator_function(
            lambda value, info: GraphObjectPydanticUtils.pydantic_validate_impl(cls, value),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: GraphObjectPydanticUtils.pydantic_serialize_impl(instance),
                return_schema=core_schema.any_schema(),
            )
        )

    @staticmethod
    @lru_cache(maxsize=128)
    def get_pydantic_properties_schema_impl(cls) -> Dict[str, Any]:
        """Generate Pydantic schema for GraphObject properties."""
        if not PYDANTIC_V2_AVAILABLE:
            raise ImportError("Pydantic v2 is required for this functionality")
            
        from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
        
        properties = cls.get_allowed_domain_properties()
        schema_properties = {}
        
        for prop_info in properties:
            prop_uri = prop_info['uri']
            prop_class = prop_info['prop_class']
            
            # Map VitalSigns property class to Pydantic schema
            prop_schema = GraphObjectPydanticUtils.map_property_to_schema_impl(prop_class)
            
            # All properties are optional in VitalSigns
            schema_properties[prop_uri] = {
                "anyOf": [prop_schema, {"type": "null"}],
                "default": None
            }
        
        return schema_properties

    @staticmethod
    def map_property_to_schema_impl(prop_class: Type) -> Dict[str, Any]:
        """Map VitalSigns property class to Pydantic core schema."""
        if not PYDANTIC_V2_AVAILABLE:
            raise ImportError("Pydantic v2 is required for this functionality")
            
        from pydantic_core import core_schema
        
        type_mapping = {
            'StringProperty': core_schema.str_schema(),
            'IntegerProperty': core_schema.int_schema(),
            'LongProperty': core_schema.int_schema(),
            'FloatProperty': core_schema.float_schema(),
            'DoubleProperty': core_schema.float_schema(),
            'BooleanProperty': core_schema.bool_schema(),
            'TruthProperty': core_schema.bool_schema(),
            'DateTimeProperty': core_schema.datetime_schema(),
            'URIProperty': core_schema.str_schema(),
            'GeoLocationProperty': core_schema.str_schema(),
            'MultiValueProperty': core_schema.list_schema(core_schema.any_schema()),
            'OtherProperty': core_schema.any_schema(),
        }
        
        return type_mapping.get(prop_class.__name__, core_schema.str_schema())

    @staticmethod
    def pydantic_validate_impl(cls, value: Any) -> 'GraphObject':
        """Validate and create GraphObject instance for Pydantic using full property URIs."""
        if isinstance(value, cls):
            return value
        elif isinstance(value, dict):
            # Create instance and set properties using full URIs
            instance = cls()
            
            # Set properties using full URI keys (for extended classes with rich property sets)
            for prop_uri, prop_value in value.items():
                if prop_value is not None:
                    GraphObjectPydanticUtils.set_property_from_pydantic_impl(instance, prop_uri, prop_value)
            
            return instance
        else:
            raise ValueError(f"Cannot convert {type(value)} to {cls.__name__}")

    @staticmethod
    def pydantic_serialize_impl(graph_object) -> Dict[str, Any]:
        """Serialize GraphObject to dict for Pydantic using full property URIs."""
        from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
        
        result = {}
        
        # Get all properties for this class from ontology
        properties = graph_object.get_allowed_domain_properties()
        
        for prop_info in properties:
            prop_uri = prop_info['uri']
            
            # Try to get value using full URI first (canonical approach)
            try:
                value = graph_object.my_getattr(prop_uri)
            except AttributeError:
                # Fallback to short name if full URI access fails
                trait_class = VitalSignsImpl.get_trait_class_from_uri(prop_uri)
                if trait_class:
                    try:
                        value = graph_object.my_getattr(trait_class.get_short_name())
                    except AttributeError:
                        continue  # Property not set
                else:
                    continue
            
            if value is not None:
                # Extract raw value using comprehensive property handling
                extracted_value = GraphObjectPydanticUtils.extract_property_value_impl(value)
                if extracted_value is not None:
                    # Use full URI as key for extended class compatibility
                    result[prop_uri] = extracted_value
        
        # Always include URI if present (special VitalSigns property)
        uri_prop_uri = "http://vital.ai/ontology/vital-core#URIProp"
        try:
            uri_value = graph_object.my_getattr(uri_prop_uri)
            if uri_value is not None:
                result[uri_prop_uri] = GraphObjectPydanticUtils.extract_property_value_impl(uri_value)
        except AttributeError:
            # Fallback to short name access
            try:
                uri_value = graph_object.my_getattr('URI')
                if uri_value is not None:
                    result[uri_prop_uri] = GraphObjectPydanticUtils.extract_property_value_impl(uri_value)
            except AttributeError:
                pass
        
        # Include vitaltype for class identification
        vitaltype_uri = "http://vital.ai/ontology/vital-core#vitaltype"
        try:
            vitaltype_value = graph_object.my_getattr(vitaltype_uri)
            if vitaltype_value is not None:
                result[vitaltype_uri] = GraphObjectPydanticUtils.extract_property_value_impl(vitaltype_value)
        except AttributeError:
            try:
                vitaltype_value = graph_object.my_getattr('vitaltype')
                if vitaltype_value is not None:
                    result[vitaltype_uri] = GraphObjectPydanticUtils.extract_property_value_impl(vitaltype_value)
            except AttributeError:
                pass
            
        return result

    @staticmethod
    def extract_property_value_impl(prop_value: Any) -> Any:
        """Extract raw value from VitalSigns property instances."""
        from vital_ai_vitalsigns.model.properties.IProperty import IProperty
        from vital_ai_vitalsigns.model.properties.MultiValueProperty import MultiValueProperty
        from vital_ai_vitalsigns.model.properties.DateTimeProperty import DateTimeProperty
        from vital_ai_vitalsigns.model.properties.GeoLocationProperty import GeoLocationProperty
        from datetime import datetime
        
        if prop_value is None:
            return None
        
        # Handle VitalSigns AttributeComparisonProxy and similar proxy objects
        if hasattr(prop_value, '__class__') and 'Proxy' in prop_value.__class__.__name__:
            # Try to get the underlying value from proxy objects
            if hasattr(prop_value, '_value'):
                prop_value = prop_value._value
            elif hasattr(prop_value, 'value'):
                prop_value = prop_value.value
            elif hasattr(prop_value, 'get_value'):
                try:
                    prop_value = prop_value.get_value()
                except:
                    # If get_value fails, convert to string
                    return str(prop_value) if prop_value is not None else None
            else:
                # Last resort: convert proxy to string
                return str(prop_value) if prop_value is not None else None
        
        # Handle all IProperty subclasses (StringProperty, IntegerProperty, etc.)
        if isinstance(prop_value, IProperty):
            try:
                # MultiValueProperty has special handling for lists
                if isinstance(prop_value, MultiValueProperty):
                    return prop_value.get_value()  # Returns list
                
                # DateTimeProperty needs special serialization for Pydantic
                elif isinstance(prop_value, DateTimeProperty):
                    datetime_val = prop_value.get_value()
                    # Return datetime object for Pydantic to handle properly
                    return datetime_val if isinstance(datetime_val, datetime) else datetime_val
                
                # GeoLocationProperty and other special types
                elif isinstance(prop_value, GeoLocationProperty):
                    return prop_value.get_value()  # Returns string representation
                
                # All other IProperty subclasses (StringProperty, IntegerProperty, etc.)
                else:
                    return prop_value.get_value()
            except Exception:
                # If get_value fails, return None
                return None
        
        # Handle CombinedProperty instances (if they exist)
        elif hasattr(prop_value, 'get_value'):
            try:
                return prop_value.get_value()
            except Exception:
                return None
        
        # Handle raw values that are already in correct format
        elif isinstance(prop_value, (str, int, float, bool, datetime, list)):
            return prop_value
        
        # Handle special VitalSigns values
        elif hasattr(prop_value, '__str__'):
            str_value = str(prop_value)
            # Skip problematic values
            if str_value in ('NotImplemented', 'NotSet', ''):
                return None
            return str_value
        
        # Fallback to None for unhandleable objects
        else:
            return None

    @staticmethod
    def set_property_from_pydantic_impl(graph_object, prop_uri: str, value: Any) -> None:
        """Set property value from Pydantic validation using full URI with proper type conversion."""
        from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
        from datetime import datetime
        
        if value is None:
            setattr(graph_object, prop_uri, None)
            return
        
        # Get property information from ontology
        properties = graph_object.get_allowed_domain_properties()
        prop_class = None
        
        # Find the property class for this URI
        for prop_info in properties:
            if prop_info['uri'] == prop_uri:
                prop_class = prop_info['prop_class']
                break
        
        # If we found property metadata, use it for proper type conversion
        if prop_class:
            # Handle different property types with proper conversion
            try:
                # Let VitalSigns handle the property creation and validation using full URI
                # The existing __setattr__ method will create the appropriate property instance
                setattr(graph_object, prop_uri, value)
            except (TypeError, ValueError) as e:
                # If direct setting fails, try type conversion based on property class
                converted_value = GraphObjectPydanticUtils.convert_value_for_property_class_impl(value, prop_class)
                setattr(graph_object, prop_uri, converted_value)
        else:
            # For unknown properties, try setting directly (may work for GraphContainerObject)
            try:
                setattr(graph_object, prop_uri, value)
            except AttributeError:
                # Property not allowed for this class type
                pass

    @staticmethod
    def convert_value_for_property_class_impl(value: Any, prop_class: Type) -> Any:
        """Convert Pydantic value to appropriate type for VitalSigns property class."""
        from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
        from vital_ai_vitalsigns.model.properties.IntegerProperty import IntegerProperty
        from vital_ai_vitalsigns.model.properties.FloatProperty import FloatProperty
        from vital_ai_vitalsigns.model.properties.DoubleProperty import DoubleProperty
        from vital_ai_vitalsigns.model.properties.LongProperty import LongProperty
        from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
        from vital_ai_vitalsigns.model.properties.DateTimeProperty import DateTimeProperty
        from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
        from vital_ai_vitalsigns.model.properties.GeoLocationProperty import GeoLocationProperty
        from vital_ai_vitalsigns.model.properties.TruthProperty import TruthProperty
        from vital_ai_vitalsigns.model.properties.MultiValueProperty import MultiValueProperty
        from datetime import datetime
        
        # Handle None values
        if value is None:
            return None
            
        # Handle special VitalSigns values that shouldn't be converted
        if isinstance(value, str) and value in ('NotImplemented', 'NotSet', ''):
            return None
        
        # Handle conversion based on property class type
        if prop_class == StringProperty:
            return str(value) if value is not None else None
        
        elif prop_class == IntegerProperty:
            try:
                if isinstance(value, str) and value.strip() == '':
                    return None
                return int(value) if value is not None else None
            except (ValueError, TypeError):
                # If conversion fails, return None instead of raising error
                return None
        
        elif prop_class in (FloatProperty, DoubleProperty):
            try:
                if isinstance(value, str) and value.strip() == '':
                    return None
                return float(value) if value is not None else None
            except (ValueError, TypeError):
                return None
        
        elif prop_class == LongProperty:
            try:
                if isinstance(value, str) and value.strip() == '':
                    return None
                return int(value) if value is not None else None
            except (ValueError, TypeError):
                return None
        
        elif prop_class == BooleanProperty:
            try:
                if isinstance(value, str):
                    if value.lower() in ('true', '1', 'yes', 'on'):
                        return True
                    elif value.lower() in ('false', '0', 'no', 'off', ''):
                        return False
                    else:
                        return None
                return bool(value) if value is not None else None
            except (ValueError, TypeError):
                return None
        
        elif prop_class == DateTimeProperty:
            try:
                if isinstance(value, datetime):
                    return value
                elif isinstance(value, str):
                    if value.strip() == '':
                        return None
                    try:
                        return datetime.fromisoformat(value)
                    except ValueError:
                        try:
                            return datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except ValueError:
                            return None
                elif isinstance(value, (int, float)):
                    return datetime.fromtimestamp(value / 1000 if value > 1e10 else value)
                else:
                    return None
            except (ValueError, TypeError):
                return None
        
        elif prop_class == URIProperty:
            return str(value) if value is not None and str(value).strip() != '' else None
        
        elif prop_class == GeoLocationProperty:
            return str(value) if value is not None and str(value).strip() != '' else None
        
        elif prop_class == TruthProperty:
            try:
                if isinstance(value, str):
                    if value.lower() in ('true', '1', 'yes', 'on'):
                        return True
                    elif value.lower() in ('false', '0', 'no', 'off', ''):
                        return False
                    else:
                        return None
                return bool(value) if value is not None else None
            except (ValueError, TypeError):
                return None
        
        elif prop_class == MultiValueProperty:
            # For multi-value properties, ensure we have a list
            if isinstance(value, list):
                return value
            elif value is not None and str(value).strip() != '':
                return [value]  # Wrap single value in list
            else:
                return []
        
        # Default: return value as-is, but handle problematic values
        if isinstance(value, str) and value.strip() == '':
            return None
        return value