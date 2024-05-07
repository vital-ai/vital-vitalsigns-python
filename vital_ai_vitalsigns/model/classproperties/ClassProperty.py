
class ClassProperty:

    def __init__(self, class_uri: str, property_uri: str):
        self._class_uri = class_uri
        self._property_uri = property_uri

    # use for cases like: VITAL_Node.name
    # which can be used for query constraints

