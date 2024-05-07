from vital_ai_vitalsigns.vectordb import InMemoryExactNNVectorDB, HNSWVectorDB
from docarray import BaseDoc, DocList
from docarray.typing import NdArray
from typing import List, Union, TypeVar, Generic
from tempfile import TemporaryDirectory

T = TypeVar('T', bound=BaseDoc)


class VectorCollectionImpl:

    def __init__(self, schema: T):
        """
                Initializes the VectorCollectionImpl with a specific schema and workspace.
                :param schema: A subclass of BaseDoc defining the schema for the database.
                """
        self.schema = schema

        temp_dir = TemporaryDirectory()
        self.temp_dir = temp_dir

        # self.db = HNSWVectorDB[schema](workspace=temp_dir.name)
        self.db = InMemoryExactNNVectorDB[schema](workspace=temp_dir.name)

    def index_documents(self, documents: DocList[T]):
        """
        Indexes a list of documents in the vector database.
        :param documents: A DocList containing documents to be indexed.
        """
        self.db.index(documents)

    def search(self, query_embedding: NdArray, limit: int = 10) -> List[T]:
        """
        Searches the vector database for the closest matches to the provided embedding.
        :param query_embedding: A vector used to search for similar documents.
        :param limit: The maximum number of results to return.
        :return: A list of objects matching the query.
        """
        query_doc = self.schema(embedding=query_embedding)

        results = self.db.search(query_doc, limit=limit)

        return results if results else []

    def remove_doc(self, doc_id: str):
        self.db.delete([doc_id])