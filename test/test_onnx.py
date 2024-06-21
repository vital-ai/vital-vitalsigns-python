import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer
import pkg_resources

model_id = 'sentence-transformers/paraphrase-MiniLM-L3-v2'

# local_path = '/Users/hadfield/Local/vital-git/vital-vitalsigns-python/models/tokenizer'
# tokenizer = AutoTokenizer.from_pretrained(model_id)
# tokenizer.save_pretrained(local_path)
# tokenizer = AutoTokenizer.from_pretrained(model_id)


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


def encode(texts):

    tokenizer = AutoTokenizer.from_pretrained(get_models_directory() + '/tokenizer')

    package_name = 'vital-model-paraphrase-MiniLM-onnx'
    model_name = 'paraphrase-MiniLM-L3-v2.onnx'

    ort_session = ort.InferenceSession(get_model_file(package_name, model_name))

    inputs = tokenizer(texts, return_tensors="np", padding=True, truncation=True)
    # Ensure only the expected inputs are passed
    ort_inputs = {k: v for k, v in inputs.items() if k in ['input_ids', 'attention_mask']}
    ort_outs = ort_session.run(None, ort_inputs)
    # Assuming the correct output index for sentence embeddings is last or determined by inspection
    sentence_embeddings = ort_outs[-1]  # Adjust this index if necessary
    return sentence_embeddings


def main():

    texts = ["This is an example sentence.", "This is another example."]
    embeddings = encode(texts)

    print(embeddings)

    print(f"Shape of sentence embeddings: {embeddings.shape}")

    for idx, embedding in enumerate(embeddings):
        print(f"Shape of embedding {idx}: {embedding.shape}")


if __name__ == "__main__":
    main()
