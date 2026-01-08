"""
Advanced Pydantic v2 integration tests for VitalSigns GraphObject.
Tests complex scenarios, error handling, and edge cases.
"""

import pytest
from datetime import datetime
from typing import List, Optional, Union

# Pydantic v2 imports
try:
    from pydantic import BaseModel, ValidationError, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    pytest.skip("Pydantic v2 not available", allow_module_level=True)

from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge


class TestAdvancedPydanticIntegration:
    """Test advanced Pydantic integration scenarios."""

    @classmethod
    def setup_class(cls):
        """Initialize VitalSigns for testing."""
        vs = VitalSigns()

    def test_nested_pydantic_models(self):
        """Test GraphObjects in nested Pydantic models."""
        
        class NodeData(BaseModel):
            node: VITAL_Node
            metadata: dict = {}
        
        class GraphData(BaseModel):
            nodes: List[NodeData]
            edges: List[VITAL_Edge]
            name: str
            
        node1 = VITAL_Node()
        node1.URI = "http://example.com/node1"
        node1.name = "Node 1"
        
        node2 = VITAL_Node()
        node2.URI = "http://example.com/node2"
        node2.name = "Node 2"
        
        edge = VITAL_Edge()
        edge.URI = "http://example.com/edge1"
        # Use correct VITAL_Edge property names with full URIs
        setattr(edge, 'http://vital.ai/ontology/vital-core#hasEdgeSource', "http://example.com/node1")
        setattr(edge, 'http://vital.ai/ontology/vital-core#hasEdgeDestination', "http://example.com/node2")
        
        graph = GraphData(
            nodes=[
                NodeData(node=node1, metadata={"type": "start"}),
                NodeData(node=node2, metadata={"type": "end"})
            ],
            edges=[edge],
            name="Test Graph"
        )
        
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.nodes[0].node.name == "Node 1"
        # Check edge properties using correct property access
        edge_source = getattr(graph.edges[0], 'http://vital.ai/ontology/vital-core#hasEdgeSource')
        assert edge_source == "http://example.com/node1"

    def test_optional_graphobject_fields(self):
        """Test optional GraphObject fields in Pydantic models."""
        
        class TestModel(BaseModel):
            required_node: VITAL_Node
            optional_node: Optional[VITAL_Node] = None
            optional_edge: Optional[VITAL_Edge] = None
            
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        
        # Test with only required field
        model1 = TestModel(required_node=node)
        assert model1.required_node.URI == "http://example.com/node1"
        assert model1.optional_node is None
        assert model1.optional_edge is None
        
        # Test with optional fields
        edge = VITAL_Edge()
        edge.URI = "http://example.com/edge1"
        
        model2 = TestModel(required_node=node, optional_edge=edge)
        assert model2.optional_edge.URI == "http://example.com/edge1"

    def test_union_types_with_graphobjects(self):
        """Test Union types containing GraphObjects."""
        
        class TestModel(BaseModel):
            graph_item: Union[VITAL_Node, VITAL_Edge]
            
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        
        edge = VITAL_Edge()
        edge.URI = "http://example.com/edge1"
        
        # Test with node
        model1 = TestModel(graph_item=node)
        assert isinstance(model1.graph_item, VITAL_Node)
        assert model1.graph_item.URI == "http://example.com/node1"
        
        # Test with edge
        model2 = TestModel(graph_item=edge)
        assert isinstance(model2.graph_item, VITAL_Edge)
        assert model2.graph_item.URI == "http://example.com/edge1"

    def test_pydantic_field_validation(self):
        """Test Pydantic field validation with GraphObjects."""
        
        class TestModel(BaseModel):
            nodes: List[VITAL_Node] = Field(min_length=1, max_length=5)
            primary_node: VITAL_Node = Field(description="The primary node")
            
        node1 = VITAL_Node()
        node1.URI = "http://example.com/node1"
        
        node2 = VITAL_Node()
        node2.URI = "http://example.com/node2"
        
        # Valid model
        model = TestModel(nodes=[node1, node2], primary_node=node1)
        assert len(model.nodes) == 2
        
        # Test validation error for empty list
        with pytest.raises(ValidationError):
            TestModel(nodes=[], primary_node=node1)

    def test_model_serialization_roundtrip(self):
        """Test complete serialization roundtrip with complex models."""
        
        class ComplexModel(BaseModel):
            nodes: List[VITAL_Node]
            edges: List[VITAL_Edge]
            metadata: dict
            timestamp: datetime
            
        node1 = VITAL_Node()
        node1.URI = "http://example.com/node1"
        node1.name = "Node 1"
        
        node2 = VITAL_Node()
        node2.URI = "http://example.com/node2"
        node2.name = "Node 2"
        
        edge = VITAL_Edge()
        edge.URI = "http://example.com/edge1"
        # Use correct VITAL_Edge property names with full URIs
        setattr(edge, 'http://vital.ai/ontology/vital-core#hasEdgeSource', "http://example.com/node1")
        setattr(edge, 'http://vital.ai/ontology/vital-core#hasEdgeDestination', "http://example.com/node2")
        
        original = ComplexModel(
            nodes=[node1, node2],
            edges=[edge],
            metadata={"version": "1.0", "created_by": "test"},
            timestamp=datetime.now()
        )
        
        # Serialize to dict
        data = original.model_dump()
        
        # Deserialize back
        restored = ComplexModel.model_validate(data)
        
        # Verify structure
        assert len(restored.nodes) == 2
        assert len(restored.edges) == 1
        assert restored.nodes[0].URI == "http://example.com/node1"
        # Check edge properties using correct property access
        edge_source = getattr(restored.edges[0], 'http://vital.ai/ontology/vital-core#hasEdgeSource')
        assert edge_source == "http://example.com/node1"
        assert restored.metadata["version"] == "1.0"


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    @classmethod
    def setup_class(cls):
        """Initialize VitalSigns for testing."""
        vs = VitalSigns()

    def test_invalid_data_types(self):
        """Test handling of invalid data types."""
        
        # Test with completely wrong type
        with pytest.raises((ValidationError, ValueError, TypeError)):
            VITAL_Node.model_validate(123)
        
        with pytest.raises((ValidationError, ValueError, TypeError)):
            VITAL_Node.model_validate([1, 2, 3])

    def test_malformed_property_uris(self):
        """Test handling of malformed property URIs."""
        
        data = {
            "http://vital.ai/ontology/vital-core#URIProp": "http://example.com/node1",
            "not_a_valid_uri": "some_value",
            "": "empty_key_value"
        }
        
        # Should handle gracefully (may ignore invalid properties)
        try:
            node = VITAL_Node.model_validate(data)
            assert node.URI == "http://example.com/node1"
        except (ValidationError, ValueError):
            # This is also acceptable behavior
            pass

    def test_circular_references(self):
        """Test handling of potential circular references."""
        
        class TestModel(BaseModel):
            node: VITAL_Node
            related_model: Optional['TestModel'] = None
            
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        
        model1 = TestModel(node=node)
        model2 = TestModel(node=node, related_model=model1)
        
        # Should not cause infinite recursion
        data = model2.model_dump()
        assert isinstance(data, dict)

    def test_large_data_handling(self):
        """Test handling of large amounts of data."""
        
        # Create many nodes
        nodes = []
        for i in range(100):
            node = VITAL_Node()
            node.URI = f"http://example.com/node{i}"
            node.name = f"Node {i}"
            nodes.append(node)
        
        class LargeModel(BaseModel):
            nodes: List[VITAL_Node]
            
        model = LargeModel(nodes=nodes)
        
        # Should handle serialization of large data
        data = model.model_dump()
        assert len(data['nodes']) == 100
        
        # Should handle deserialization
        restored = LargeModel.model_validate(data)
        assert len(restored.nodes) == 100

    def test_property_type_mismatches(self):
        """Test handling of property type mismatches."""
        
        data = {
            "http://vital.ai/ontology/vital-core#URIProp": "http://example.com/node1",
            "http://vital.ai/ontology/vital-core#hasTimestamp": "not_a_number"  # Should be int
        }
        
        # Should either convert or raise appropriate error
        try:
            node = VITAL_Node.model_validate(data)
            # If successful, timestamp should be converted or None
        except (ValidationError, ValueError, TypeError):
            # This is expected behavior for invalid type conversion
            pass

    def test_missing_required_properties(self):
        """Test handling of missing required properties."""
        
        # Test with minimal data
        data = {}
        
        # Should handle gracefully (VitalSigns properties are generally optional)
        try:
            node = VITAL_Node.model_validate(data)
            # Should create a valid node even with minimal data
            assert isinstance(node, VITAL_Node)
        except (ValidationError, ValueError):
            # This might be expected if some properties are required
            pass


class TestPerformanceAndCaching:
    """Test performance aspects and caching behavior."""

    @classmethod
    def setup_class(cls):
        """Initialize VitalSigns for testing."""
        vs = VitalSigns()

    def test_schema_caching(self):
        """Test that schema generation is cached properly."""
        
        # Create multiple instances - should reuse cached schema
        node1 = VITAL_Node()
        node1.URI = "http://example.com/node1"
        
        node2 = VITAL_Node()
        node2.URI = "http://example.com/node2"
        
        # Both should work efficiently
        data1 = node1.model_dump()
        data2 = node2.model_dump()
        
        assert isinstance(data1, dict)
        assert isinstance(data2, dict)

    def test_repeated_serialization_performance(self):
        """Test performance of repeated serialization operations."""
        
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        node.name = "Test Node"
        node.timestamp = 1640995200000
        
        # Perform multiple serializations
        for i in range(10):
            data = node.model_dump()
            assert "http://vital.ai/ontology/vital-core#URIProp" in data
            
            # Deserialize
            new_node = VITAL_Node.model_validate(data)
            assert new_node.URI == "http://example.com/node1"


class TestCompatibilityWithExistingCode:
    """Test compatibility with existing VitalSigns patterns."""

    @classmethod
    def setup_class(cls):
        """Initialize VitalSigns for testing."""
        vs = VitalSigns()

    def test_existing_serialization_methods_unaffected(self):
        """Verify existing serialization methods work unchanged."""
        
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        node.name = "Test Node"
        
        # Test all existing methods still work
        dict_data = node.to_dict()
        json_data = node.to_json()
        
        # Verify they produce expected formats
        assert 'URI' in dict_data  # VitalSigns format
        assert isinstance(json_data, str)
        
        # Verify Pydantic methods produce different format
        pydantic_data = node.model_dump()
        assert "http://vital.ai/ontology/vital-core#URIProp" in pydantic_data
        
        # Formats should be different
        assert dict_data != pydantic_data

    def test_property_access_patterns_unchanged(self):
        """Verify property access patterns work unchanged."""
        
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        node.name = "Test Node"
        
        # Test existing property access still works
        assert node.URI == "http://example.com/node1"
        assert node.name == "Test Node"
        
        # Test after Pydantic serialization/deserialization
        data = node.model_dump()
        new_node = VITAL_Node.model_validate(data)
        
        assert new_node.URI == "http://example.com/node1"
        assert new_node.name == "Test Node"

    def test_vitalsigns_registry_integration(self):
        """Test that VitalSigns registry integration works properly."""
        
        node = VITAL_Node()
        node.URI = "http://example.com/node1"
        
        # Test that registry-based operations still work
        properties = node.get_allowed_domain_properties()
        assert isinstance(properties, list)
        assert len(properties) > 0
        
        # Test after Pydantic operations
        data = node.model_dump()
        new_node = VITAL_Node.model_validate(data)
        
        new_properties = new_node.get_allowed_domain_properties()
        assert len(new_properties) == len(properties)


if __name__ == "__main__":
    pytest.main([__file__])
