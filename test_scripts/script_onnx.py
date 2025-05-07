import onnxruntime as ort
from transformers import AutoTokenizer
from importlib.resources import files  # Python 3.9+ / built-in 3.11


# local_path = '/Users/hadfield/Local/vital-git/vital-vitalsigns-python/models/tokenizer'
# tokenizer = AutoTokenizer.from_pretrained(model_id)
# tokenizer.save_pretrained(local_path)
# tokenizer = AutoTokenizer.from_pretrained(model_id)


model_id = 'sentence-transformers/paraphrase-MiniLM-L3-v2'


def get_models_directory() -> str:
    """
    Return the filesystem path to 'models/' inside 'vital_ai_vitalsigns'.
    """
    try:
        # files() returns a Traversable, str(...) yields a real path
        return str(files('vital_ai_vitalsigns').joinpath('models'))
    except ModuleNotFoundError as e:
        raise FileNotFoundError(
            "The 'models' directory was not found in the 'vital_ai_vitalsigns' package."
        ) from e


def get_model_file(package_name: str, file_name: str) -> str:
    """
    Return the filesystem path to 'model/<file_name>' inside the given package.
    """
    try:
        return str(files(package_name).joinpath('model', file_name))
    except ModuleNotFoundError as e:
        raise FileNotFoundError(
            f"The file {file_name!r} was not found in the 'model/' directory of package {package_name!r}."
        ) from e


def encode(texts):
    # Load tokenizer from local 'models/tokenizer'
    tokenizer = AutoTokenizer.from_pretrained(get_models_directory() + '/tokenizer')

    # Initialize ONNX session
    package_name = 'vital-model-paraphrase-MiniLM-onnx'
    model_name = 'paraphrase-MiniLM-L3-v2.onnx'
    ort_session = ort.InferenceSession(get_model_file(package_name, model_name))

    # Tokenize and run inference
    inputs = tokenizer(texts, return_tensors="np", padding=True, truncation=True)
    ort_inputs = {k: v for k, v in inputs.items() if k in ('input_ids', 'attention_mask')}
    ort_outs = ort_session.run(None, ort_inputs)
    # Use the last output tensor as the embedding
    return ort_outs[-1]


def main():
    texts = ["This is an example sentence.", "This is another example."]
    embeddings = encode(texts)

    print(embeddings)
    print(f"Shape of sentence embeddings: {embeddings.shape}")
    for idx, emb in enumerate(embeddings):
        print(f"Shape of embedding {idx}: {emb.shape}")


if __name__ == "__main__":
    main()
