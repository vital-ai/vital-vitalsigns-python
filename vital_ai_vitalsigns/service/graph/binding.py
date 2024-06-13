from enum import Enum


class BindingValueType(Enum):
    LITERAL = "literal-binding-value"
    URIREF = "uriref-binding-value"


class Binding:
    def __init__(self,
                 variable: str,
                 property_uri: str,
                 value_type: BindingValueType = BindingValueType.URIREF,
                 optional: bool = False, unbound_symbol: str = "UNKNOWN"):
        self.variable = variable
        self.property_uri = property_uri
        self.value_type = value_type
        self.optional = optional
        self.unbound_symbol = unbound_symbol



