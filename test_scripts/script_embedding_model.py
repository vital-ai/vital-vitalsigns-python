from vital_ai_vitalsigns.embedding.embedding_model import EmbeddingModel
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean

import numpy as np


def main():
    print('Hello World')

    vs = VitalSigns()

    embedder = EmbeddingModel()

    # text1 = "This is a test sentence."
    # vector1 = embedder.vectorize(text1)
    #print(f"Vector for single sentence: {vector1}")

    # texts = ["This is the first test sentence.", "Here is another one."]
    # vectors = embedder.vectorize(texts)
    # print(f"Vectors for multiple sentences: {vectors}")

    sentence1 = "The cat sits on the mat."
    sentence2 = "A kitten is sitting on a carpet."
    sentence3 = "The stock market is experiencing a decline."

    # Encode the sentences into vectors
    vector1 = embedder.vectorize(sentence1)
    vector2 = embedder.vectorize(sentence2)
    vector3 = embedder.vectorize(sentence3)

    # Normalize vectors to unit length
    vector1 /= np.linalg.norm(vector1)
    vector2 /= np.linalg.norm(vector2)
    vector3 /= np.linalg.norm(vector3)

    # Combine vectors into a single array for comparison
    vectors = np.array([vector1, vector2, vector3])

    # Compute pairwise cosine similarity
    similarity_matrix = cosine_similarity(vectors)

    # Print the similarity matrix
    print("Pairwise Cosine Similarity:")
    print(similarity_matrix)

    # Interpret the results
    print("\nInterpretation:")
    print(f"Similarity between Sentence 1 and Sentence 2 (related): {similarity_matrix[0, 1]:.4f}")
    print(f"Similarity between Sentence 1 and Sentence 3 (unrelated): {similarity_matrix[0, 2]:.4f}")
    print(f"Similarity between Sentence 2 and Sentence 3 (unrelated): {similarity_matrix[1, 2]:.4f}")

    dist12 = euclidean(vector1, vector2)
    dist13 = euclidean(vector1, vector3)
    dist23 = euclidean(vector2, vector3)


    print(f"Euclidean distance between Sentence 1 and Sentence 2: {dist12}")
    print(f"Euclidean distance between Sentence 1 and Sentence 3: {dist13}")
    print(f"Euclidean distance between Sentence 2 and Sentence 3: {dist23}")

    # Global normalization based on the maximum theoretical distance
    max_distance = np.sqrt(2)  # Theoretical max distance for normalized embeddings on a unit sphere

    # Normalize distances to [0, 1]
    normalized_dist12 = dist12 / max_distance
    normalized_dist13 = dist13 / max_distance
    normalized_dist23 = dist23 / max_distance

    print("\nGlobal Normalized Distances:")
    print(f"Normalized distance between Sentence 1 and Sentence 2: {normalized_dist12:.4f}")
    print(f"Normalized distance between Sentence 1 and Sentence 3: {normalized_dist13:.4f}")
    print(f"Normalized distance between Sentence 2 and Sentence 3: {normalized_dist23:.4f}")

    # Convert distances to global similarity scores
    similarity12 = 1 - normalized_dist12
    similarity13 = 1 - normalized_dist13
    similarity23 = 1 - normalized_dist23

    print("\nGlobal Similarity Scores:")
    print(f"Similarity score between Sentence 1 and Sentence 2: {similarity12:.4f}")
    print(f"Similarity score between Sentence 1 and Sentence 3: {similarity13:.4f}")
    print(f"Similarity score between Sentence 2 and Sentence 3: {similarity23:.4f}")


if __name__ == "__main__":
    main()
