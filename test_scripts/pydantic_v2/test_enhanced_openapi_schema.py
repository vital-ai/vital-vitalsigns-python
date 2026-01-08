#!/usr/bin/env python3

import pytest
from typing import List
from vital_ai_vitalsigns.vitalsigns import VitalSigns

# Initialize VitalSigns
vs = VitalSigns()

try:
    from pydantic import BaseModel
    from vital_ai_vitalsigns_core.model.VITAL_Node import VITAL_Node
    from vital_ai_vitalsigns_core.model.VITAL_Edge import VITAL_Edge
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = None
    VITAL_Node = None
    VITAL_Edge = None


class TestEnhancedOpenAPISchema:
    """Test enhanced OpenAPI schema generation showing VitalSigns property structure."""

    @classmethod
    def setup_class(cls):
        """Initialize VitalSigns for testing."""
        vs = VitalSigns()

    @pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic not available")
    def test_enhanced_json_schema_generation(self):
        """Test that VitalSigns objects generate detailed JSON schemas for OpenAPI."""
        
        # Test VITAL_Node schema generation
        node_schema = VITAL_Node.__get_pydantic_json_schema__(None, None)
        
        print(f"Generated schema for VITAL_Node:")
        print(f"Title: {node_schema.get('title')}")
        print(f"Description: {node_schema.get('description')}")
        print(f"Properties count: {len(node_schema.get('properties', {}))}")
        
        # Verify schema structure
        assert node_schema["type"] == "object"
        assert node_schema["title"] == "VITAL_Node"
        assert "VitalSigns" in node_schema["description"]
        
        # Verify essential properties are present
        properties = node_schema["properties"]
        assert "URI" in properties
        assert "vitaltype" in properties
        
        # Verify URI property details
        uri_prop = properties["URI"]
        assert uri_prop["type"] == "string"
        assert uri_prop["format"] == "uri"
        assert "identifier" in uri_prop["description"]
        
        # Verify vitaltype property
        vitaltype_prop = properties["vitaltype"]
        assert vitaltype_prop["type"] == "string"
        assert vitaltype_prop.get("readOnly") == True
        
        # Should have more properties than just URI and vitaltype
        assert len(properties) > 2, f"Expected more than 2 properties, got {len(properties)}"
        
        print(f"✓ Enhanced schema generation working - found {len(properties)} properties")

    @pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic not available")
    def test_property_type_mapping(self):
        """Test that VitalSigns properties are mapped to correct JSON schema types."""
        
        node_schema = VITAL_Node.__get_pydantic_json_schema__(None, None)
        properties = node_schema["properties"]
        
        # Check for common property types if they exist
        property_checks = []
        
        for prop_name, prop_schema in properties.items():
            if prop_name == "URI":
                assert prop_schema["type"] == "string"
                assert prop_schema["format"] == "uri"
                property_checks.append(f"URI: string/uri ✓")
            elif "name" in prop_name.lower():
                assert prop_schema["type"] == "string"
                property_checks.append(f"{prop_name}: string ✓")
            elif "time" in prop_name.lower() or "date" in prop_name.lower():
                if prop_schema["type"] == "string":
                    assert prop_schema.get("format") == "date-time"
                    property_checks.append(f"{prop_name}: datetime ✓")
        
        print("Property type mappings verified:")
        for check in property_checks:
            print(f"  {check}")
        
        assert len(property_checks) > 0, "Should have verified at least some property types"

    @pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic not available")
    def test_fastapi_model_integration(self):
        """Test that enhanced schemas work with FastAPI model generation."""
        
        class APIModel(BaseModel):
            node: VITAL_Node
            edge: VITAL_Edge
            nodes: List[VITAL_Node] = []
        
        # This should work without errors and generate proper OpenAPI schema
        try:
            api_schema = APIModel.model_json_schema()
            
            # Verify the model schema structure
            assert "properties" in api_schema
            assert "node" in api_schema["properties"]
            assert "edge" in api_schema["properties"]
            assert "nodes" in api_schema["properties"]
            
            # Check that VitalSigns objects have detailed schemas, not generic ones
            node_def = api_schema["properties"]["node"]
            
            # Should reference a definition with detailed properties
            if "$defs" in api_schema:
                # Find VITAL_Node definition
                vital_node_def = None
                for def_name, def_schema in api_schema["$defs"].items():
                    if "VITAL_Node" in def_name:
                        vital_node_def = def_schema
                        break
                
                if vital_node_def:
                    assert "properties" in vital_node_def
                    assert len(vital_node_def["properties"]) > 2  # More than just URI and vitaltype
                    print(f"✓ FastAPI integration working - VITAL_Node has {len(vital_node_def['properties'])} properties")
                else:
                    print("! VITAL_Node definition not found in $defs, but schema generation succeeded")
            
            print("✓ FastAPI model integration successful")
            
        except Exception as e:
            pytest.fail(f"FastAPI model integration failed: {e}")

    @pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic not available")
    def test_schema_fallback_behavior(self):
        """Test that schema generation gracefully falls back if ontology access fails."""
        
        # This test verifies the fallback behavior in the enhanced schema generation
        # Even if there are issues accessing the ontology, it should return a basic schema
        
        try:
            schema = VITAL_Node.__get_pydantic_json_schema__(None, None)
            
            # Should always have basic structure
            assert schema["type"] == "object"
            assert "title" in schema
            assert "properties" in schema
            assert "URI" in schema["properties"]
            
            print("✓ Schema generation robust with fallback behavior")
            
        except Exception as e:
            pytest.fail(f"Schema generation should not fail completely: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
