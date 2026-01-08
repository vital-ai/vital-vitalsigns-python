"""
Basic Pydantic v2 integration tests for VitalSigns GraphObject.
"""

import pytest
from datetime import datetime
from typing import List

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


class TestPydanticBasicIntegration:
    """Test basic Pydantic v2 integration with GraphObject instances."""

    @classmethod
    def setup_class(cls):
        """Initialize VitalSigns for testing."""
        vs = VitalSigns()

    def test_graphobject_in_pydantic_model(self):
        """Test GraphObject as field in Pydantic model."""
        
        class TestModel(BaseModel):
            node: VITAL_Node
            edge: VITAL_Edge
            
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        node.name = "Test Node"
        
        edge = VITAL_Edge()
        edge.URI = "http://example.com/edge1"
        
        model = TestModel(node=node, edge=edge)
        
        assert model.node.URI == "http://example.com/node1"
        assert model.node.name == "Test Node"
        assert model.edge.URI == "http://example.com/edge1"

    def test_model_dump_with_full_uris(self):
        """Test Pydantic model_dump method returns full property URIs."""
        
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        node.name = "Test Node"
        node.timestamp = 1640995200000
        
        data = node.model_dump()
        
        assert isinstance(data, dict)
        # Verify full URIs are used as keys
        assert "http://vital.ai/ontology/vital-core#URIProp" in data
        assert "http://vital.ai/ontology/vital-core#hasName" in data
        assert "http://vital.ai/ontology/vital-core#hasTimestamp" in data
        
        assert data["http://vital.ai/ontology/vital-core#URIProp"] == "http://example.com/node1"
        assert data["http://vital.ai/ontology/vital-core#hasName"] == "Test Node"
        assert data["http://vital.ai/ontology/vital-core#hasTimestamp"] == 1640995200000

    def test_model_validate_with_full_uris(self):
        """Test Pydantic model_validate method with full property URIs."""
        
        data = {
            "http://vital.ai/ontology/vital-core#URIProp": "http://example.com/node1",
            "http://vital.ai/ontology/vital-core#hasName": "Test Node",
            "http://vital.ai/ontology/vital-core#hasTimestamp": 1640995200000
        }
        
        node = VITAL_Node.model_validate(data)
        
        assert node.URI == "http://example.com/node1"
        assert node.name == "Test Node"
        assert node.timestamp == 1640995200000

    def test_model_dump_json(self):
        """Test JSON serialization through Pydantic."""
        
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        node.name = "Test Node"
        
        json_str = node.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "http://vital.ai/ontology/vital-core#URIProp" in json_str
        assert "http://example.com/node1" in json_str

    def test_model_validate_json(self):
        """Test JSON validation through Pydantic."""
        
        json_data = '''
        {
            "http://vital.ai/ontology/vital-core#URIProp": "http://example.com/node1",
            "http://vital.ai/ontology/vital-core#hasName": "Test Node"
        }
        '''
        
        node = VITAL_Node.model_validate_json(json_data)
        
        assert node.URI == "http://example.com/node1"
        assert node.name == "Test Node"

    def test_roundtrip_serialization(self):
        """Test complete roundtrip: create -> serialize -> validate -> verify."""
        
        # Create original node
        original = VITAL_Node()
        original.URI = "http://example.com/node1"
        original.name = "Test Node"
        original.timestamp = 1640995200000
        
        # Serialize to dict
        data = original.model_dump()
        
        # Validate back to object
        restored = VITAL_Node.model_validate(data)
        
        # Verify properties match
        assert restored.URI == original.URI
        assert restored.name == original.name
        assert restored.timestamp == original.timestamp

    def test_none_property_handling(self):
        """Test handling of None/null property values."""
        
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        # Don't set other properties (they should be None)
        
        # Test serialization with None values
        data = node.model_dump()
        assert "http://vital.ai/ontology/vital-core#URIProp" in data
        assert data["http://vital.ai/ontology/vital-core#URIProp"] == "http://example.com/node1"
        
        # Test deserialization with explicit None
        data_with_null = {
            "http://vital.ai/ontology/vital-core#URIProp": "http://example.com/node1",
            "http://vital.ai/ontology/vital-core#hasName": None,
            "http://vital.ai/ontology/vital-core#hasTimestamp": None
        }
        
        new_node = VITAL_Node.model_validate(data_with_null)
        assert new_node.URI == "http://example.com/node1"
        # Note: VitalSigns may not set properties to None explicitly

    def test_pydantic_validation_errors(self):
        """Test that invalid data raises appropriate Pydantic validation errors."""
        
        # Test with invalid data type
        with pytest.raises((ValidationError, ValueError)):
            VITAL_Node.model_validate("invalid_data")
        
        # Test with invalid JSON
        with pytest.raises((ValidationError, ValueError)):
            VITAL_Node.model_validate_json("invalid json")


class TestPydanticListHandling:
    """Test Pydantic handling of lists of GraphObjects."""

    @classmethod
    def setup_class(cls):
        """Initialize VitalSigns for testing."""
        vs = VitalSigns()

    def test_list_of_graphobjects_in_pydantic_model(self):
        """Test list of GraphObjects in Pydantic model."""
        
        class TestModel(BaseModel):
            nodes: List[VITAL_Node]
            
        node1 = VITAL_Node()
        node1.URI = "http://example.com/node1"
        node1.name = "Node 1"
        
        node2 = VITAL_Node()
        node2.URI = "http://example.com/node2"
        node2.name = "Node 2"
        
        model = TestModel(nodes=[node1, node2])
        
        assert len(model.nodes) == 2
        assert model.nodes[0].URI == "http://example.com/node1"
        assert model.nodes[1].URI == "http://example.com/node2"

    def test_mixed_graphobject_types(self):
        """Test mixed GraphObject types in Pydantic model."""
        
        class TestModel(BaseModel):
            node: VITAL_Node
            edge: VITAL_Edge
            
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        
        edge = VITAL_Edge()
        edge.URI = "http://example.com/edge1"
        # Use correct VITAL_Edge property names
        setattr(edge, 'http://vital.ai/ontology/vital-core#hasEdgeSource', "http://example.com/node1")
        setattr(edge, 'http://vital.ai/ontology/vital-core#hasEdgeDestination', "http://example.com/node2")
        
        model = TestModel(node=node, edge=edge)
        
        assert isinstance(model.node, VITAL_Node)
        assert isinstance(model.edge, VITAL_Edge)
        # Check edge properties using correct property access
        edge_source = getattr(edge, 'http://vital.ai/ontology/vital-core#hasEdgeSource')
        assert edge_source == "http://example.com/node1"


class TestOpenAPISchemaGeneration:
    """Test that reproduces the production API OpenAPI schema generation error."""

    @classmethod
    def setup_class(cls):
        """Initialize VitalSigns for testing."""
        vs = VitalSigns()

    def test_fastapi_openapi_schema_generation_error(self):
        """Test that reproduces the 'AttributeComparisonProxy' object is not callable error."""
        try:
            from pydantic import BaseModel
            from pydantic.json_schema import GenerateJsonSchema
            from pydantic._internal._generate_schema import GenerateSchema
            from pydantic._internal._config import ConfigWrapper
            
            class APIModel(BaseModel):
                node: VITAL_Node
                edge: VITAL_Edge
                nodes: List[VITAL_Node] = []
            
            # This should trigger the same error as the production API
            # when FastAPI tries to generate OpenAPI schema
            try:
                schema = APIModel.model_json_schema()
                # If this succeeds, the error is fixed
                assert isinstance(schema, dict)
                print("✓ OpenAPI schema generation successful - error is fixed")
                
                # Verify the schema has expected structure
                assert 'properties' in schema
                assert 'node' in schema['properties']
                assert 'edge' in schema['properties']
                assert 'nodes' in schema['properties']
                
            except TypeError as e:
                if "'AttributeComparisonProxy' object is not callable" in str(e):
                    # This is the exact error we're trying to reproduce and fix
                    print(f"✗ Reproduced production API error: {e}")
                    raise e
                elif "argument of type 'NoneType' is not iterable" in str(e):
                    # This suggests our fix is returning None when Pydantic expects a proper schema
                    print(f"✗ Fix is incomplete - Pydantic expects proper schema handler: {e}")
                    raise e
                else:
                    # Different error, re-raise it
                    raise e
                
        except ImportError:
            pytest.skip("Pydantic schema generation testing requires full Pydantic installation")

    def test_pydantic_attributes_raise_attribute_error(self):
        """Test that Pydantic-specific attributes raise AttributeError instead of returning AttributeComparisonProxy."""
        
        # Test that most Pydantic attributes raise AttributeError on GraphObject classes
        # Note: __get_pydantic_json_schema__ and __get_pydantic_core_schema__ are now implemented
        pydantic_attrs_should_raise = [
            '__pydantic_generic_metadata__',
            '__pydantic_serializer__',
            '__pydantic_validator__',
            '__pydantic_decorators__',
            '__pydantic_fields__'
        ]
        
        for attr in pydantic_attrs_should_raise:
            with pytest.raises(AttributeError):
                getattr(VITAL_Node, attr)
        
        # Test that implemented Pydantic methods exist and are callable
        assert hasattr(VITAL_Node, '__get_pydantic_json_schema__')
        assert hasattr(VITAL_Node, '__get_pydantic_core_schema__')
        assert callable(getattr(VITAL_Node, '__get_pydantic_json_schema__'))
        assert callable(getattr(VITAL_Node, '__get_pydantic_core_schema__'))
                
        print(f"✓ Pydantic attributes properly handled - some raise AttributeError, others are implemented")


if __name__ == "__main__":
    pytest.main([__file__])
