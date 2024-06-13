from vital_ai_vitalsigns.collection.graph_collection import GraphCollection
from typing import List, Union, TypeVar, Generic
from tempfile import TemporaryDirectory
import hnswlib
import numpy as np


class VectorCollectionImpl:

    def __init__(self, graph: GraphCollection):
        """
        Initializes the VectorCollectionImpl with a specific schema and workspace.
        """

        embedding_vector_size = 384
        max_size = 100000

        self.graph = graph
        self.index = hnswlib.Index(space='cosine', dim=embedding_vector_size)

        self.index.init_index(max_elements=max_size, ef_construction=200, M=16)

        # self.index.set_ef(100)

        self.current_index = 0
        self.doc_id_to_index = {}
        self.index_to_doc_id = {}

    def index_documents(self, documents):
        """
        Indexes a list of documents in the vector database.
        :param documents: A DocList containing documents to be indexed.
        """
        # self.db.index(documents)

    def search(self, query_embedding, class_uri: str = None, limit: int = 10) -> List:
        """
        Searches the vector database for the closest matches to the provided embedding.
        :param class_uri:
        :param query_embedding: A vector used to search for similar documents.
        :param limit: The maximum number of results to return.
        :return: A list of objects matching the query.
        """

        search_vector = query_embedding  # np.array(search_vector, dtype=np.float32)
        # search_vector /= np.linalg.norm(search_vector)

        self.index.set_ef(50)

        current_count = self.index.element_count
        print(f"Current number of elements in the index: {current_count}")

        k = limit

        if k > current_count:
            k = current_count

        # print(f"Index space: { self.index.space}, dimension: { self.index.dim}")
        # print(f"Max elements: { self.index.max_elements}, M: { self.index.M}, ef_construction: { self.index.ef_construction}")

        # print(search_vector)

        # model_id = 'paraphrase-MiniLM-L3-v2'
        # model = SentenceTransformer(model_id)

        # new_sentence = "A new sentence similar to the previous ones"
        # new_embedding = model.encode([new_sentence])

        # labels, distances = self.index.knn_query(new_embedding, k=1)

        labels, distances = self.index.knn_query(query_embedding, k=k)

        # print(labels[0][0])
        # print(distances[0][0])

        results = {
            'matches': [],
            'scores': []
        }

        # print(self.index_to_doc_id)
        # print(self.doc_id_to_index)

        for label, score in zip(labels[0], distances[0]):
            doc_id = self.index_to_doc_id.get(label, None)
            # print(f"doc_id: {doc_id}")
            if doc_id:
                results['matches'].append({'URI': doc_id})
                results['scores'].append(score)

        return results


        """
        if class_uri is None:
            query_doc = self.schema(embedding=query_embedding)

            results = self.db.search(query_doc, limit=limit)

            return results if results else []
        else:
            query_doc = self.schema(embedding=query_embedding)

            results = self.db.filter(query_doc, limit=limit, ClassURI=class_uri)

            return results if results else []
        """

    def remove_doc(self, doc_id: str):
        self.db.delete([doc_id])