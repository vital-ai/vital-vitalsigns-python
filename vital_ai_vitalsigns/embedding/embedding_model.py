from sentence_transformers import SentenceTransformer
from typing import List, Union, Dict
import hashlib
from collections import OrderedDict
import logging
import numpy as np


class LRUEmbeddingCache:
    def __init__(self, maxsize=1000):
        self.cache = OrderedDict()
        self.maxsize = maxsize

    def get(self, key: str):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: List[float]):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)


class EmbeddingModel:
    def __init__(self, model_id: str = 'paraphrase-MiniLM-L3-v2', cache_size=1000):
        # self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        # self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.model_id = model_id
        self.model = SentenceTransformer(model_id)
        self.cache = LRUEmbeddingCache(maxsize=cache_size)

    def get_model_id(self):
        return self.model_id

    def hash_text(self, text: str) -> str:
        # Create a SHA-256 hash of the text
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def vectorize(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Vectorize a single string or a list of strings using the model.
        :param text: A string or a list of strings to be vectorized.
        :return: A list of floats (if single string) or list of list of floats (if multiple strings).
        """
        single_string = False
        if isinstance(text, str):
            text = [text]
            single_string = True

        # Create a list to hold results
        results = []
        uncached_texts = []

        for t in text:
            hash_key = self.hash_text(t)
            cached_vector = self.cache.get(hash_key)
            if cached_vector is not None:
                results.append(cached_vector)
            else:
                uncached_texts.append(t)

        logging.info(f"Cached Vector Count: {len(results)} Uncached Vector Count: {len(uncached_texts)}")

        if uncached_texts:
            new_embeddings = self.model.encode(uncached_texts)
            for t, vector in zip(uncached_texts, new_embeddings):
                hash_key = self.hash_text(t)
                self.cache.set(hash_key, vector)
                results.append(vector)

        if single_string:
            """
            obj = results[0]
            if isinstance(obj, np.ndarray):
                # Print type and shape for NumPy arrays
                print(f"Type: {type(obj)}, Shape: {obj.shape}")
            else:
                # Print only the type for other data types
                print(f"Type: {type(obj)}")
            """
            return results[0]

        return results
