from typing import List
from vital_ai_vitalsigns.service.vector.vector_service import VitalVectorService

# Note: this will expose creating collections based on passed in schema
# via WeaviateCollectionDefinition
# the schema will determine the content of the vectors

# requests will need to check if tenant exists for a collection, and if
# not, add it

class WeaviateVectorService(VitalVectorService):

    def __init__(self):
        super().__init__()

    def get_collection_identifiers(self) -> List[str]:

        collection_identifier_list = []

        return collection_identifier_list
