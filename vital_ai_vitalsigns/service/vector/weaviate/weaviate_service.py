from vital_ai_vitalsigns.service.vector.vector_service import VitalVectorService


class WeaviateVectorService(VitalVectorService):
    pass

# Note: this will expose creating collections based on passed in schema
# via WeaviateCollectionDefinition
# the schema will determine the content of the vectors

# requests will need to check if tenant exists for a collection, and if
# not, add it

