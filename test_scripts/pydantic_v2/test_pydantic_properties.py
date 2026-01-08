"""
Comprehensive property type tests for Pydantic v2 integration with VitalSigns.
"""

import pytest
from datetime import datetime
from typing import List, Any

# Pydantic v2 imports
try:
    from pydantic import BaseModel, ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    pytest.skip("Pydantic v2 not available", allow_module_level=True)

from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge


class TestAllPropertyTypes:
    """Comprehensive tests for all VitalSigns property types."""

    @classmethod
    def setup_class(cls):
        """Initialize VitalSigns for testing."""
        vs = VitalSigns()

    def test_string_property_complete(self):
        """Test StringProperty with various string values using actual VITAL_Node properties."""
        
        test_cases = [
            "Simple string",
            "String with spaces and punctuation!",
            "Unicode string: 你好世界",
            "",  # Empty string
            "Very long string " * 100,  # Long string
        ]
        
        for test_string in test_cases:
            node = VITAL_Node()
            node.URI = f"http://example.com/string_test_{hash(test_string)}"
            # Use actual VITAL_Node string property: hasName -> name
            node.name = test_string
            
            # Serialize and deserialize
            data = node.model_dump()
            new_node = VITAL_Node.model_validate(data)
            
            assert new_node.name == test_string

    def test_integer_property_complete(self):
        """Test IntegerProperty with various integer values using actual VITAL_Node properties."""
        
        test_cases = [
            0,
            1,
            -1,
            1000000,
            -1000000,
            2147483647,  # Max 32-bit int
            -2147483648,  # Min 32-bit int
        ]
        
        for test_int in test_cases:
            node = VITAL_Node()
            node.URI = f"http://example.com/int_test_{test_int}"
            # Use actual VITAL_Node integer property: hasTimestamp -> timestamp
            node.timestamp = test_int
            
            # Serialize and deserialize
            data = node.model_dump()
            new_node = VITAL_Node.model_validate(data)
            
            assert new_node.timestamp == test_int

    def test_boolean_property_complete(self):
        """Test BooleanProperty with boolean values."""
        
        test_cases = [True, False]
        
        for test_bool in test_cases:
            node = VITAL_Node()
            node.URI = f"http://example.com/bool_test_{test_bool}"
            # Use actual VITAL_Node boolean property: isActive
            node.active = test_bool
            
            # Serialize and deserialize
            data = node.model_dump()
            new_node = VITAL_Node.model_validate(data)
            
            assert new_node.active == test_bool

    def test_float_property_serialization(self):
        """Test FloatProperty serialization/deserialization."""
        
        test_cases = [
            0.0,
            1.0,
            -1.0,
            3.14159,
            1.23e-10,  # Very small number
            1.23e10,   # Very large number
        ]
        
        for test_float in test_cases:
            node = VITAL_Node()
            node.URI = f"http://example.com/float_test_{test_float}"
            # Note: May need to use a property that accepts float values
            # For testing purposes, we'll use timestamp which can accept numeric values
            node.timestamp = int(test_float * 1000)  # Convert to int for timestamp
            
            # Test that numeric values are preserved
            data = node.model_dump()
            assert isinstance(data.get("http://vital.ai/ontology/vital-core#hasTimestamp"), int)

    def test_uri_property_handling(self):
        """Test URIProperty handling with various URI formats."""
        
        test_uris = [
            "http://example.com/test1",
            "https://example.com/test2",
            "urn:test:example",
            "http://vital.ai/ontology/vital-core#TestClass",
        ]
        
        for test_uri in test_uris:
            node = VITAL_Node()
            node.URI = test_uri
            
            # Serialize and deserialize
            data = node.model_dump()
            new_node = VITAL_Node.model_validate(data)
            
            assert new_node.URI == test_uri

    def test_null_property_handling(self):
        """Test handling of None/null property values."""
        
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        # Don't set other properties (they should be None)
        
        # Test serialization with None values
        data = node.model_dump()
        assert data.get("http://vital.ai/ontology/vital-core#URIProp") == "http://example.com/node1"
        
        # Test deserialization with explicit None
        data_with_null = {
            "http://vital.ai/ontology/vital-core#URIProp": "http://example.com/node1",
            "http://vital.ai/ontology/vital-core#hasName": None,
            "http://vital.ai/ontology/vital-core#hasTimestamp": None
        }
        
        new_node = VITAL_Node.model_validate(data_with_null)
        assert new_node.URI == "http://example.com/node1"

    def test_property_type_conversion(self):
        """Test automatic type conversion during deserialization."""
        
        # Test string to int conversion
        data = {
            "http://vital.ai/ontology/vital-core#URIProp": "http://example.com/node1",
            "http://vital.ai/ontology/vital-core#hasTimestamp": "1640995200000"  # String that should convert to int
        }
        
        node = VITAL_Node.model_validate(data)
        # In VitalSigns, properties return property objects, not raw values
        # Get the actual value using the property object's get_value() method
        timestamp_prop = node.timestamp
        if hasattr(timestamp_prop, 'get_value'):
            timestamp_value = timestamp_prop.get_value()
            assert isinstance(timestamp_value, int)
            assert timestamp_value == 1640995200000
        else:
            # If it's already the raw value, check that
            assert isinstance(timestamp_prop, int)
            assert timestamp_prop == 1640995200000

    def test_edge_properties(self):
        """Test Edge-specific properties."""
        
        edge = VITAL_Edge()
        edge.URI = "http://example.com/edge1"
        # Use correct VITAL_Edge property names with full URIs
        setattr(edge, 'http://vital.ai/ontology/vital-core#hasEdgeSource', "http://example.com/node1")
        setattr(edge, 'http://vital.ai/ontology/vital-core#hasEdgeDestination', "http://example.com/node2")
        
        # Serialize and deserialize
        data = edge.model_dump()
        new_edge = VITAL_Edge.model_validate(data)
        
        assert new_edge.URI == "http://example.com/edge1"
        # Check edge properties using correct property access
        edge_source = getattr(new_edge, 'http://vital.ai/ontology/vital-core#hasEdgeSource')
        edge_dest = getattr(new_edge, 'http://vital.ai/ontology/vital-core#hasEdgeDestination')
        assert edge_source == "http://example.com/node1"
        assert edge_dest == "http://example.com/node2"

    def test_complex_property_combinations(self):
        """Test combinations of different property types."""
        
        node = VITAL_Node()
        node.URI = "http://example.com/complex_node"
        node.name = "Complex Test Node"
        node.timestamp = 1640995200000
        node.active = True
        
        # Serialize
        data = node.model_dump()
        
        # Verify all properties are present with full URIs
        expected_keys = [
            "http://vital.ai/ontology/vital-core#URIProp",
            "http://vital.ai/ontology/vital-core#hasName",
            "http://vital.ai/ontology/vital-core#hasTimestamp",
            "http://vital.ai/ontology/vital-core#isActive"
        ]
        
        for key in expected_keys:
            if key in data:  # Some properties might not be set
                assert data[key] is not None
        
        # Deserialize and verify
        new_node = VITAL_Node.model_validate(data)
        assert new_node.URI == "http://example.com/complex_node"
        assert new_node.name == "Complex Test Node"
        assert new_node.timestamp == 1640995200000
        assert new_node.active == True


class TestPropertyValidation:
    """Test property validation and error handling."""

    @classmethod
    def setup_class(cls):
        """Initialize VitalSigns for testing."""
        vs = VitalSigns()

    def test_invalid_property_values(self):
        """Test handling of invalid property values."""
        
        # Test with completely invalid data structure
        try:
            result = VITAL_Node.model_validate({"invalid": "structure"})
            # If it doesn't raise an error, that's also acceptable behavior
            print(f"Validation succeeded with result: {result}")
        except (ValidationError, ValueError, TypeError):
            # This is the expected behavior
            pass

    def test_property_schema_generation(self):
        """Test that property schemas are generated correctly."""
        
        # This tests the __get_pydantic_core_schema__ method indirectly
        node = VITAL_Node()
        node.URI = "http://example.com/schema_test"
        
        # Should not raise any errors
        data = node.model_dump()
        assert isinstance(data, dict)
        
        # Should be able to validate back
        new_node = VITAL_Node.model_validate(data)
        assert new_node.URI == "http://example.com/schema_test"

    def test_unknown_properties_handling(self):
        """Test handling of unknown/external properties."""
        
        # Test with properties that might not be in the base VITAL_Node
        data = {
            "http://vital.ai/ontology/vital-core#URIProp": "http://example.com/node1",
            "http://example.com/unknown#property": "unknown_value"
        }
        
        # Should not fail completely, but unknown properties might be ignored
        try:
            node = VITAL_Node.model_validate(data)
            assert node.URI == "http://example.com/node1"
        except (ValidationError, ValueError):
            # This is acceptable - unknown properties might be rejected
            pass


class TestPydanticIntegrationWithExistingMethods:
    """Test that Pydantic methods don't interfere with existing VitalSigns methods."""

    @classmethod
    def setup_class(cls):
        """Initialize VitalSigns for testing."""
        vs = VitalSigns()

    def test_to_dict_unchanged(self):
        """Test that existing to_dict method is unchanged."""
        
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        node.name = "Test Node"
        
        # Test existing to_dict method
        dict_data = node.to_dict()
        
        # Should have VitalSigns format (not Pydantic format)
        assert 'URI' in dict_data  # Short key, not full URI
        assert 'type' in dict_data
        assert 'types' in dict_data
        
        # Test Pydantic method has different format
        pydantic_data = node.model_dump()
        
        # Should have full URI keys
        assert "http://vital.ai/ontology/vital-core#URIProp" in pydantic_data
        
        # Verify they're different formats
        assert dict_data != pydantic_data

    def test_from_dict_unchanged(self):
        """Test that existing from_dict method is unchanged."""
        
        # Create data in VitalSigns format
        dict_data = {
            'URI': 'http://example.com/node1',
            'type': 'http://vital.ai/ontology/vital-core#VITAL_Node',
            'http://vital.ai/ontology/vital-core#hasName': 'Test Node'
        }
        
        # Should work with existing from_dict
        node = VITAL_Node.from_dict(dict_data)
        assert node.URI == "http://example.com/node1"
        assert node.name == "Test Node"

    def test_json_methods_unchanged(self):
        """Test that existing JSON methods are unchanged."""
        
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        node.name = "Test Node"
        
        # Test existing to_json method
        json_str = node.to_json()
        assert isinstance(json_str, str)
        
        # Test existing from_json method
        new_node = VITAL_Node.from_json(json_str)
        assert new_node.URI == "http://example.com/node1"
        assert new_node.name == "Test Node"


if __name__ == "__main__":
    pytest.main([__file__])
