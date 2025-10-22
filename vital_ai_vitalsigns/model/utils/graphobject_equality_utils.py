from __future__ import annotations

from typing import Optional


class GraphObjectEqualityUtils:
    """Utility class containing equality comparison functionality for GraphObject."""

    @staticmethod
    def equals(graph_object_a: 'GraphObject', graph_object_b: 'GraphObject') -> bool:
        """
        Compare two GraphObjects for equality.
        
        Two GraphObjects are considered equal if they have:
        1. The same set of properties (including URI)
        2. All properties have equal values
        3. Same extern properties (for GraphContainerObjects)
        
        Args:
            graph_object_a: First GraphObject to compare
            graph_object_b: Second GraphObject to compare
            
        Returns:
            bool: True if the objects are equal, False otherwise
        """
        # Handle null cases
        if graph_object_a is None and graph_object_b is None:
            return True
        if graph_object_a is None or graph_object_b is None:
            return False
            
        # Check if both objects are of the same type
        if type(graph_object_a) != type(graph_object_b):
            return False
            
        # Compare main properties
        if not GraphObjectEqualityUtils._compare_properties(
            graph_object_a._properties, 
            graph_object_b._properties
        ):
            return False
            
        # Compare extern properties for GraphContainerObjects
        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
        
        is_container_a = isinstance(graph_object_a, VITAL_GraphContainerObject)
        is_container_b = isinstance(graph_object_b, VITAL_GraphContainerObject)
        
        # Both should be containers or both should not be containers
        if is_container_a != is_container_b:
            return False
            
        if is_container_a and is_container_b:
            if not GraphObjectEqualityUtils._compare_properties(
                graph_object_a._extern_properties,
                graph_object_b._extern_properties
            ):
                return False
                
        return True
    
    @staticmethod
    def _compare_properties(props_a: dict, props_b: dict) -> bool:
        """
        Compare two property dictionaries for equality.
        
        Args:
            props_a: First property dictionary
            props_b: Second property dictionary
            
        Returns:
            bool: True if properties are equal, False otherwise
        """
        # Check if both dictionaries have the same keys
        if set(props_a.keys()) != set(props_b.keys()):
            return False
            
        # Compare each property value
        for key in props_a.keys():
            prop_a = props_a[key]
            prop_b = props_b[key]
            
            # Handle None cases
            if prop_a is None and prop_b is None:
                continue
            if prop_a is None or prop_b is None:
                return False
                
            # Compare property values using their to_json representation
            # This ensures consistent comparison across different property types
            try:
                value_a = prop_a.to_json()["value"] if hasattr(prop_a, 'to_json') else prop_a
                value_b = prop_b.to_json()["value"] if hasattr(prop_b, 'to_json') else prop_b
                
                if value_a != value_b:
                    return False
            except Exception:
                # Fallback to direct comparison if to_json fails
                if prop_a != prop_b:
                    return False
                    
        return True