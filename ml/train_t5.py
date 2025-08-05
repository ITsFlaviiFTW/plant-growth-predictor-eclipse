import pandas as pd
from transformers import T5Tokenizer, T5ForConditionalGeneration, AdamW
import torch
from torch.utils.data import DataLoader, Dataset

class SuggestionDataset(Dataset):
    def __init__(self, prompts, responses, tokenizer, max_input_len=64, max_output_len=128):
        self.prompts = prompts
        self.responses = responses
        self.tokenizer = tokenizer
        self.max_input_len = max_input_len
        self.max_output_len = max_output_len

    def __len__(self):
        return len(self.prompts)

    def __getitem__(self, idx):
        input_enc = self.tokenizer(
            self.prompts[idx],
            max_length=self.max_input_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        target_enc = self.tokenizer(
            self.responses[idx],
            max_length=self.max_output_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        return {
            "input_ids": input_enc["input_ids"].squeeze(0),
            "attention_mask": input_enc["attention_mask"].squeeze(0),
            "labels": target_enc["input_ids"].squeeze(0)
        }

# Load data
df = pd.read_csv("ml/suggestion_dataset.csv").dropna()
prompts = df["prompt"].tolist()
responses = df["response"].tolist()

# Model + tokenizer
model = T5ForConditionalGeneration.from_pretrained("t5-small")
tokenizer = T5Tokenizer.from_pretrained("t5-small")

# Dataset + loader
dataset = SuggestionDataset(prompts, responses, tokenizer)
loader = DataLoader(dataset, batch_size=8, shuffle=True)

# Optimizer
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
optimizer = AdamW(model.parameters(), lr=3e-4)

# Training loop
epochs = 5
model.train()
for epoch in range(epochs):
    total_loss = 0
    for batch in loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        total_loss += loss.item()

    print(f"Epoch {epoch + 1} loss: {total_loss:.4f}")

# Save model
model.save_pretrained("ml/t5_suggestion_model")
tokenizer.save_pretrained("ml/t5_suggestion_model")
print("Trained model saved to ml/t5_suggestion_model/")
