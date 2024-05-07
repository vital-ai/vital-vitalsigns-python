from sentence_transformers import SentenceTransformer
from typing import List, Union


class EmbeddingModel:
    def __init__(self, model_id: str = 'paraphrase-MiniLM-L3-v2'):
        # self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        # self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.model_id = model_id
        self.model = SentenceTransformer(model_id)

    def get_model_id(self):
        return self.model_id

    def vectorize(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Vectorize a single string or a list of strings using the model.
        :param text: A string or a list of strings to be vectorized.
        :return: A list of floats (if single string) or list of list of floats (if multiple strings).
        """
        # Ensure input is a list for batch processing
        if isinstance(text, str):
            text = [text]

        # Get embeddings
        embeddings = self.model.encode(text)

        # Return a single embedding if input was a single string
        if len(embeddings) == 1:
            return embeddings[0]

        return embeddings
