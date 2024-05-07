from vital_ai_vitalsigns.vectordb.db.base import VectorDB
from vital_ai_vitalsigns.vectordb.db.executors.hnsw_indexer import HNSWLibIndexer


class HNSWVectorDB(VectorDB):
    _executor_type = HNSWLibIndexer
    reverse_score_order = False
