from transformers import T5Tokenizer, T5ForConditionalGeneration

model_path = "ml/t5_finetuned/checkpoint-471"
tokenizer = T5Tokenizer.from_pretrained(model_path)
model = T5ForConditionalGeneration.from_pretrained(model_path)

def generate_suggestion(prompt: str) -> str:
    inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=64)
    output = model.generate(**inputs, max_length=128, num_beams=4, early_stopping=True)
    return tokenizer.decode(output[0], skip_special_tokens=True)
