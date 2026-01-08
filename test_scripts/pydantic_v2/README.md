# Pydantic v2 Integration Tests

This directory contains comprehensive tests for the Pydantic v2 compatibility implementation in VitalSigns GraphObject classes.

## Overview

The Pydantic v2 integration enables VitalSigns GraphObject instances to work seamlessly with Pydantic models, providing:

- Native Pydantic v2 compatibility
- Full property URI serialization for extended classes
- Comprehensive property type support
- Zero interference with existing VitalSigns functionality

## Test Structure

### Basic Integration Tests (`test_pydantic_basic.py`)
- GraphObject as fields in Pydantic models
- Basic serialization/deserialization with `model_dump()` and `model_validate()`
- JSON serialization with `model_dump_json()` and `model_validate_json()`
- Roundtrip serialization testing
- List handling and validation errors

### Property Type Tests (`test_pydantic_properties.py`)
- Comprehensive testing of all VitalSigns property types
- String, Integer, Boolean, Float, URI property handling
- Property type conversion and validation
- Edge-specific properties (sourceURI, targetURI)
- Complex property combinations
- Compatibility with existing methods (`to_dict`, `from_dict`, etc.)

### Advanced Integration Tests (`test_pydantic_advanced.py`)
- Nested Pydantic models with GraphObjects
- Optional and Union types with GraphObjects
- Field validation and constraints
- Error handling and edge cases
- Performance and caching tests
- Large data handling
- Compatibility with existing VitalSigns patterns

## Running the Tests

### Prerequisites
```bash
pip install pydantic>=2.0
pip install pytest
```

### Run All Tests
```bash
# From the project root
python -m pytest test_scripts/pydantic_v2/ -v

# Or from this directory
pytest -v
```

### Run Specific Test Files
```bash
pytest test_pydantic_basic.py -v
pytest test_pydantic_properties.py -v
pytest test_pydantic_advanced.py -v
```

### Run Specific Test Classes
```bash
pytest test_pydantic_basic.py::TestPydanticBasicIntegration -v
pytest test_pydantic_properties.py::TestAllPropertyTypes -v
```

## Key Features Tested

### ✅ Full Property URI Serialization
Tests verify that serialization uses full property URIs as keys:
```python
{
    "http://vital.ai/ontology/vital-core#URIProp": "http://example.com/node1",
    "http://vital.ai/ontology/vital-core#hasName": "Test Node"
}
```

### ✅ Extended Class Compatibility
Tests ensure the implementation works with extended classes that have rich property sets from domain ontologies.

### ✅ Non-Interfering Design
Tests verify that existing VitalSigns methods (`to_dict`, `from_dict`, `to_json`, etc.) remain completely unchanged.

### ✅ Comprehensive Property Support
Tests cover all 13 VitalSigns property types:
- StringProperty, IntegerProperty, LongProperty
- FloatProperty, DoubleProperty, BooleanProperty
- TruthProperty, DateTimeProperty, URIProperty
- GeoLocationProperty, MultiValueProperty, OtherProperty

### ✅ Error Handling
Tests verify proper handling of:
- Invalid data types
- Malformed property URIs
- Property type mismatches
- Missing properties
- Validation errors

## Expected Test Results

All tests should pass when:
1. VitalSigns is properly initialized
2. Pydantic v2 is installed
3. The GraphObject Pydantic implementation is correctly integrated

## Troubleshooting

### ImportError: Pydantic v2 not available
```bash
pip install pydantic>=2.0
```

### VitalSigns initialization errors
Ensure VitalSigns ontology files are properly loaded:
```python
vs = VitalSigns()
vs.load_ontology_from_file()
```

### Property access errors
Verify that the test properties exist in the VitalSigns ontology and are accessible on the test classes (VITAL_Node, VITAL_Edge).

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run Pydantic v2 Tests
  run: |
    pip install pydantic>=2.0 pytest
    python -m pytest test_scripts/pydantic_v2/ -v --tb=short
```

## Performance Considerations

The tests include performance checks to ensure:
- Schema generation is properly cached
- Repeated serialization operations are efficient
- Large data sets are handled appropriately
- No memory leaks in repeated operations

## Future Enhancements

Additional test scenarios that could be added:
- Integration with FastAPI applications
- Complex inheritance hierarchies
- Custom property validation rules
- Performance benchmarking
- Memory usage profiling
