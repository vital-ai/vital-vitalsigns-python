
class WeaviateCollectionDefinition:
    def __init__(self, name, vectorizer_config, description, properties):
        self.name = name
        self.vectorizer_config = vectorizer_config
        self.description = description
        self.properties = properties
