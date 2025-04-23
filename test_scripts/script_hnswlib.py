import logging
import hnswlib
import numpy as np
from vital_ai_vitalsigns.embedding.embedding_model import EmbeddingModel
# from sentence_transformers import SentenceTransformer

def main():
    logging.basicConfig(level=logging.INFO)
    logging.info('Hello World')

    # model_id = 'paraphrase-MiniLM-L3-v2'
    # model = SentenceTransformer(model_id)

    # sentences = ['This is an example sentence', 'This is another one']

    sentences = [
        "The majestic mountains were bathed in the golden hues of the setting sun.",
        "In the bustling city, skyscrapers reached toward the heavens.",
        "Artificial intelligence is transforming the landscape of modern technology.",
        "A gentle rain fell upon the quiet countryside, nourishing the fields.",
        "The chef prepared a sumptuous meal blending traditional spices with modern techniques.",
        "Ancient ruins whispered secrets of a long-forgotten civilization.",
        "The jazz band played soulful melodies in the dimly lit bar.",
        "A marathon runner pushed past physical limits to cross the finish line.",
        "The art gallery showcased abstract paintings that challenged conventional views.",
        "A curious scientist embarked on a groundbreaking experiment in a high-tech lab.",
        "The peaceful garden was filled with blooming roses and the sound of chirping birds.",
        "Under the starlit sky, campers gathered around the fire to share legends and myths.",
        "Economic forecasts indicate a period of growth and innovation in the tech sector.",
        "The novel's intricate narrative explored themes of identity and transformation.",
        "A spacecraft launched into orbit, marking a new era in space exploration.",
        "Local volunteers organized a community cleanup to beautify the neighborhood.",
        "A new restaurant opened in town, offering a unique blend of culinary traditions.",
        "The environmental summit emphasized the urgent need for sustainable practices.",
        "Historical documentaries shed light on the struggles and triumphs of the past.",
        "The athlete's victory was celebrated as a triumph of perseverance and dedication."
    ]

    # Create embeddings
    # embeddings = model.encode(sentences)

    embedder = EmbeddingModel()

    vectors_list = embedder.vectorize(sentences)
    print(f"Vectors for multiple sentences: {vectors_list}")

    vectors = np.array(vectors_list)

    print(f"Vectors for multiple sentences: {vectors}")

    # Dimension of our vector space
    dimension = vectors.shape[1]

    print(f"Dimension: {dimension}")

    # Create a new index
    p = hnswlib.Index(space='cosine', dim=dimension)

    # Initialize an index - the maximum number of elements should be known beforehand
    p.init_index(max_elements=10000, ef_construction=200, M=16)

    # Element insertion (can be called several times)
    p.add_items(vectors)

    # Controlling the recall by setting ef:
    p.set_ef(50)  # ef should always be > k

    # Query HNSW index for most similar sentence
    # new_sentence = "A new sentence similar to the previous ones"
    # new_embedding = model.encode([new_sentence])

    new_sentence = "Under a twilight sky, a soft rain caressed the ancient ruins, stirring echoes of forgotten legends."

    new_vector_list = embedder.vectorize([new_sentence])
    new_vector = np.array(new_vector_list)

    # Fetch k neighbors
    # labels, distances = p.knn_query(new_vector, k=1)

    # print("Most similar sentence is: ", sentences[labels[0][0]])

    labels, distances = p.knn_query(new_vector, k=10, num_threads=1, filter=None)

    print("Top 10 similar sentences:")

    # Loop through each result and print the sentence with its similarity score.

    for rank, (label, distance) in enumerate(zip(labels[0], distances[0])):
        # It's possible that the index contains fewer sentences than k,
        # so ensure that the label index is valid.
        if label < len(sentences):
            print(f"Rank {rank + 1}: Sentence: '{sentences[label]}', Score: {distance}")
        else:
            print(f"Rank {rank + 1}: No corresponding sentence found, Score: {distance}")


if __name__ == "__main__":
    main()
