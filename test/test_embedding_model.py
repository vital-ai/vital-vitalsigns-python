from vital_ai_vitalsigns.embedding.embedding_model import EmbeddingModel


def main():
    print('Hello World')

    embedder = EmbeddingModel()

    text1 = "This is a test sentence."
    vector1 = embedder.vectorize(text1)
    print(f"Vector for single sentence: {vector1}")

    texts = ["This is the first test sentence.", "Here is another one."]
    vectors = embedder.vectorize(texts)
    print(f"Vectors for multiple sentences: {vectors}")


if __name__ == "__main__":
    main()


