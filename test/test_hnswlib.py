import logging
from sentence_transformers import SentenceTransformer
import hnswlib
import numpy as np


def main():
    logging.basicConfig(level=logging.INFO)
    logging.info('Hello World')

    model_id = 'paraphrase-MiniLM-L3-v2'
    model = SentenceTransformer(model_id)

    sentences = ['This is an example sentence', 'This is another one']

    # Create embeddings
    embeddings = model.encode(sentences)

    # Dimension of our vector space
    dimension = embeddings.shape[1]

    print(f"Dimension: {dimension}")

    # Create a new index
    p = hnswlib.Index(space='cosine', dim=dimension)

    # Initialize an index - the maximum number of elements should be known beforehand
    p.init_index(max_elements=10000, ef_construction=200, M=16)

    # Element insertion (can be called several times)
    p.add_items(embeddings)

    # Controlling the recall by setting ef:
    p.set_ef(50)  # ef should always be > k

    # Query HNSW index for most similar sentence
    new_sentence = "A new sentence similar to the previous ones"
    new_embedding = model.encode([new_sentence])

    # Fetch k neighbors
    labels, distances = p.knn_query(new_embedding, k=1)

    print("Most similar sentence is: ", sentences[labels[0][0]])


if __name__ == "__main__":
    main()
