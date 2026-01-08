from typing import List, Union
import hashlib
from collections import OrderedDict
import logging
import numpy as np
import onnxruntime as ort
# Suppress ONNX Runtime warnings about GPU device discovery
ort.set_default_logger_severity(3)  # 3 = ERROR level, suppresses warnings
from transformers import AutoTokenizer
from importlib.resources import files  # Python 3.9+
# from sentence_transformers import SentenceTransformer


def get_models_directory() -> str:
    """
    Return the absolute filesystem path to the `models/` directory
    inside the `vital_ai_vitalsigns` package.
    """
    try:
        # files() returns a Traversable; str(...) gives a filesystem path
        return str(files('vital_ai_vitalsigns').joinpath('models'))
    except ModuleNotFoundError as e:
        raise FileNotFoundError(
            "The `models` directory could not be found in the `vital_ai_vitalsigns` package."
        ) from e


def get_model_file(package_name: str, file_name: str) -> str:
    """
    Return the absolute filesystem path to `model/<file_name>`
    inside the given `package_name`.
    """
    try:
        return str(files(package_name).joinpath('model', file_name))
    except ModuleNotFoundError as e:
        raise FileNotFoundError(
            f"The file {file_name!r} could not be found in the `model/` directory of package {package_name!r}."
        ) from e


class LRUEmbeddingCache:
    def __init__(self, maxsize: int = 1000):
        self.cache = OrderedDict()
        self.maxsize = maxsize

    def get(self, key: str) -> Union[List[float], None]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: List[float]) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)


class EmbeddingModel:
    def __init__(self, cache_size: int = 1000):
        package_name = 'vital-model-paraphrase-MiniLM-onnx'
        model_name = 'paraphrase-MiniLM-L3-v2.onnx'
        model_id = 'paraphrase-MiniLM-L3-v2'

        # Load tokenizer from local package data
        tokenizer_path = get_models_directory() + '/tokenizer'
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

        # Create an ONNXRuntime session for inference
        model_path = get_model_file(package_name, model_name)
        # Use CPU provider only to avoid GPU device discovery warnings
        providers = ['CPUExecutionProvider']
        self.ort_session = ort.InferenceSession(model_path, providers=providers)

        self.model_id = model_id
        self.cache = LRUEmbeddingCache(maxsize=cache_size)

    def get_model_id(self) -> str:
        return self.model_id

    def hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def vectorize(
        self, text: Union[str, List[str]]
    ) -> Union[List[float], List[List[float]]]:
        single_string = False
        if isinstance(text, str):
            text = [text]
            single_string = True

        results, uncached = [], []
        for t in text:
            key = self.hash_text(t)
            vec = self.cache.get(key)
            if vec is not None:
                results.append(vec)
            else:
                uncached.append(t)

        logging.info(
            f"Cached: {len(results)} | To compute: {len(uncached)}"
        )

        if uncached:
            inputs = self.tokenizer(
                uncached, return_tensors="np", padding=True, truncation=True
            )
            ort_inputs = {
                k: v for k, v in inputs.items()
                if k in ("input_ids", "attention_mask")
            }
            ort_outs = self.ort_session.run(None, ort_inputs)
            embeddings = ort_outs[-1]

            for t, vec in zip(uncached, embeddings):
                key = self.hash_text(t)
                self.cache.set(key, vec)
                results.append(vec)

        return results[0] if single_string else results
