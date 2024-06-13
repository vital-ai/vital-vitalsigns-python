from sentence_transformers import SentenceTransformer
import torch
import transformers
import numpy as np


def main():
    model_id = 'sentence-transformers/paraphrase-MiniLM-L3-v2'

    model = SentenceTransformer(model_id)

    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id)

    # Create a dummy input
    dummy_input_text = "This is a dummy input text."

    inputs = tokenizer(dummy_input_text, return_tensors="pt")

    # inputs = {key: value.cpu() for key, value in inputs.items()}

    inputs = {k: v for k, v in inputs.items() if k in ['input_ids', 'attention_mask']}

    inputs = {key: value.cpu() for key, value in inputs.items()}

    input_shape = inputs['input_ids'].shape

    dummy_input = {
        'input_ids': torch.zeros(input_shape, dtype=torch.int64).cpu(),
        'attention_mask': torch.zeros(input_shape, dtype=torch.int64).cpu()
    }

    class CustomSentenceTransformer(torch.nn.Module):
        def __init__(self, model):
            super(CustomSentenceTransformer, self).__init__()
            self.model = model

        def forward(self, input_ids, attention_mask):
            return self.model({'input_ids': input_ids, 'attention_mask': attention_mask})

    # Instantiate the custom model
    custom_model = CustomSentenceTransformer(model).cpu()

    # Export the model to ONNX
    torch.onnx.export(
        custom_model,
        (dummy_input['input_ids'], dummy_input['attention_mask']),
        "/Users/hadfield/Local/vital-git/vital-vitalsigns-python/models/paraphrase-MiniLM-L3-v2.onnx",
        input_names=['input_ids', 'attention_mask'],
        output_names=['output'],
        dynamic_axes={'input_ids': {0: 'batch_size', 1: 'sequence_length'},
                      'attention_mask': {0: 'batch_size', 1: 'sequence_length'},
                      'output': {0: 'batch_size'}}
    )


if __name__ == "__main__":
    main()
