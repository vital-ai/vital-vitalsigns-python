from typing import List
from vital_ai_vitalsigns.model.properties.IProperty import IProperty
from vital_ai_vitalsigns.model.utils.unordered_list import UnorderedList


class MultiValueProperty(IProperty):
    def __init__(self, value: list, property_class):
        self.property_class = property_class
        list_value = list(value)
        # TODO enforce values are of the property class type
        unordered_list = UnorderedList(list_value)
        super().__init__(unordered_list)

    def get_value(self) -> List:
        return self.value.to_list()

    def __eq__(self, other) -> bool:
        if isinstance(other, list):
            unordered_list = UnorderedList(other)
            return self.value == unordered_list
        elif isinstance(other, MultiValueProperty):
            return self.value == other.value
        return NotImplemented

    def __lt__(self, other) -> bool:
        if isinstance(other, list):
            unordered_list = UnorderedList(other)
            return self.value < unordered_list
        elif isinstance(other, MultiValueProperty):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other) -> bool:
        if isinstance(other, list):
            unordered_list = UnorderedList(other)
            return self.value <= unordered_list
        elif isinstance(other, MultiValueProperty):
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other) -> bool:
        if isinstance(other, list):
            unordered_list = UnorderedList(other)
            return self.value > unordered_list
        elif isinstance(other, MultiValueProperty):
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other) -> bool:
        if isinstance(other, list):
            unordered_list = UnorderedList(other)
            return self.value >= unordered_list
        elif isinstance(other, MultiValueProperty):
            return self.value >= other.value
        return NotImplemented

    def __repr__(self) -> str:
        return f"MultiValueProperty(value={self.value})"

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value.to_list()}

    def to_rdf(self):

        property_class = self.property_class

        data_class = property_class.get_data_class()

        return {"value": self.value.to_list(), "datatype": list, "data_class": data_class}


