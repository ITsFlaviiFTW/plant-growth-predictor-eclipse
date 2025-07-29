from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch

# Load the fine-tuned model
model_path = "ml/t5_finetuned"
tokenizer = T5Tokenizer.from_pretrained(model_path)
model = T5ForConditionalGeneration.from_pretrained(model_path)

def suggest(esp_id: str, prompt: str) -> dict:
    input_ids = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True).input_ids
    output = model.generate(input_ids, max_length=100, num_beams=4, early_stopping=True)
    decoded = tokenizer.decode(output[0], skip_special_tokens=True)
    return {
        "esp_id": esp_id,
        "prompt": prompt,
        "suggestion": decoded
    }
