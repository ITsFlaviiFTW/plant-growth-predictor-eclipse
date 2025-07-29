from transformers import T5Tokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments, DataCollatorForSeq2Seq
from datasets import load_dataset, Dataset
import pandas as pd

# Load CSV
df = pd.read_csv("ml/Expert_Plant_Health_DatasetV2.csv")
df = df.dropna(subset=["prompt", "response"]).reset_index(drop=True)
dataset = Dataset.from_pandas(df)

# Tokenizer & model
model_name = "t5-small"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

# Tokenize
def preprocess(example):
    model_inputs = tokenizer(
        example["prompt"],
        max_length=64,
        padding="max_length",
        truncation=True
    )
    labels = tokenizer(
        example["response"],
        max_length=128,
        padding="max_length",
        truncation=True
    )
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

tokenized = dataset.map(preprocess, batched=False, remove_columns=dataset.column_names)
collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

# Training config
args = TrainingArguments(
    output_dir="ml/t5_finetuned",
    per_device_train_batch_size=4,
    num_train_epochs=3,
    logging_steps=10,
    save_strategy="epoch",
    fp16=False
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=tokenized,
    tokenizer=tokenizer,
    data_collator=collator
)

trainer.train()
model.save_pretrained("ml/t5_finetuned")
tokenizer.save_pretrained("ml/t5_finetuned")
