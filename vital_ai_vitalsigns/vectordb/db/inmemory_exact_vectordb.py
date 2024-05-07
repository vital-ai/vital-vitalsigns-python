from vital_ai_vitalsigns.vectordb.db.base import VectorDB
from vital_ai_vitalsigns.vectordb.db.executors.inmemory_exact_indexer import InMemoryExactNNIndexer


class InMemoryExactNNVectorDB(VectorDB):
    _executor_type = InMemoryExactNNIndexer
    reverse_score_order = True
