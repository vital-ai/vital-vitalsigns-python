from vital_ai_vitalsigns.model.properties.IProperty import IProperty


class AnnotationValue(IProperty):
    def __init__(self, value: str, lang: str = None):
        super().__init__(str(value), lang=lang)

    def __eq__(self, other):
        if isinstance(other, AnnotationValue):
            return self.value == other.value and self.lang == other.lang
        if isinstance(other, str):
            return self.value == other
        return NotImplemented

    def __hash__(self):
        return hash((self.value, self.lang))

    def __repr__(self):
        if self.lang:
            return f"AnnotationValue({self.value!r}, lang={self.lang!r})"
        return f"AnnotationValue({self.value!r})"

    def __str__(self):
        return str(self.value)

    def to_json(self):
        result = {"value": self.value}
        if self.lang:
            result["lang"] = self.lang
        return result

    @classmethod
    def from_json(cls, data):
        if isinstance(data, str):
            return cls(data)
        if isinstance(data, dict):
            return cls(data["value"], lang=data.get("lang"))
        raise ValueError(f"Cannot create AnnotationValue from {type(data)}")
