from typing import List, Union, Dict
import hashlib
from collections import OrderedDict
import logging
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
import pkg_resources
# from sentence_transformers import SentenceTransformer

def get_models_directory():
    try:
        # Get the path to the models directory within vitalsigns
        models_path = pkg_resources.resource_filename('vital_ai_vitalsigns', 'models')
        return models_path
    except KeyError:
        raise FileNotFoundError("The models directory could not be found in the package.")

def get_model_file(package_name, file_name):
    try:
        # Construct the resource path
        resource_path = pkg_resources.resource_filename(package_name, f'model/{file_name}')
        return resource_path
    except KeyError:
        raise FileNotFoundError(f"The file {file_name} could not be found in the models directory.")


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
    def __init__(self, cache_size=1000):
        # self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        # self.model = SentenceTransformer('all-MiniLM-L6-v2')
        # from sentence_transformers import SentenceTransformer

        package_name = 'vital-model-paraphrase-MiniLM-onnx'
        model_name = 'paraphrase-MiniLM-L3-v2.onnx'
        model_id = 'paraphrase-MiniLM-L3-v2'

        self.tokenizer = AutoTokenizer.from_pretrained(get_models_directory() + '/tokenizer')
        self.ort_session = ort.InferenceSession(get_model_file(package_name, model_name))

        self.model_id = model_id
        # self.model = SentenceTransformer(model_id, device="cpu")
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
            if self.ort_session:
                # new_embeddings = self.model.encode(uncached_texts)

                inputs = self.tokenizer(uncached_texts, return_tensors="np", padding=True, truncation=True)
                # Ensure only the expected inputs are passed
                ort_inputs = {k: v for k, v in inputs.items() if k in ['input_ids', 'attention_mask']}

                # the default embedding model has max size 128 tokens
                ort_outs = self.ort_session.run(None, ort_inputs)
                # Assuming the correct output index for sentence embeddings is last or determined by inspection
                sentence_embeddings = ort_outs[-1]  # Adjust this index if necessary
                # return sentence_embeddings

                for t, vector in zip(uncached_texts, sentence_embeddings):
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
