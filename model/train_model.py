import torch
from datasets import load_dataset, concatenate_datasets, get_dataset_config_names
from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizer,
    Trainer,
    TrainingArguments,
)
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def train():
    DATASET_NAME = "Hello-SimpleAI/HC3"
    
    print(f"Fetching all configurations for {DATASET_NAME}...")
    all_configs = get_dataset_config_names(DATASET_NAME)
    all_configs.remove('all')
    
    print(f"Found configurations: {all_configs}")

    all_train_splits = []

    for config in all_configs:
        print(f"Loading configuration: {config}")
        try:
            subset_dataset = load_dataset(DATASET_NAME, config, split="train")
            all_train_splits.append(subset_dataset)
        except Exception as e:
            print(f"Could not load or process config {config}. Error: {e}")

    print("Combining all datasets into a single training set...")
    full_dataset = concatenate_datasets(all_train_splits)
    print(f"\nTotal examples available: {len(full_dataset)}\n")

    print("Splitting the dataset into train (90%) and evaluation (10%) sets...")
    split_dataset = full_dataset.train_test_split(test_size=0.1, seed=42)

    train_dataset = split_dataset['train'].shuffle(seed=42).select(range(1000))
    eval_dataset = split_dataset['test'].shuffle(seed=42).select(range(200))
    
    print(f"\nUsing {len(train_dataset)} examples for training.")
    print(f"Using {len(eval_dataset)} examples for evaluation.\n")

    tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

    def tokenize_and_format(examples):
        texts = []
        labels = []

        if 'human_answer' in examples and 'chatgpt_answer' in examples:
            for human, ai in zip(examples['human_answer'], examples['chatgpt_answer']):
                if human and isinstance(human, str):
                    texts.append(human)
                    labels.append(0)
                if ai and isinstance(ai, str):
                    texts.append(ai)
                    labels.append(1)

        elif 'human_answers' in examples and 'chatgpt_answers' in examples:
            for human_list, ai_list in zip(examples['human_answers'], examples['chatgpt_answers']):
                for human_text in human_list:
                    if human_text and isinstance(human_text, str):
                        texts.append(human_text)
                        labels.append(0)
                for ai_text in ai_list:
                    if ai_text and isinstance(ai_text, str):
                        texts.append(ai_text)
                        labels.append(1)

        elif 'answer' in examples and 'source' in examples:
            for answer, source in zip(examples['answer'], examples['source']):
                if not (answer and isinstance(answer, str)):
                    continue
                if source in ['reddit', 'webtext', 'human']:
                    texts.append(answer)
                    labels.append(0)
                elif source == 'chatgpt':
                    texts.append(answer)
                    labels.append(1)
        
        else:
            raise ValueError(f"Dataset batch has an unexpected structure. Columns found: {list(examples.keys())}")

        tokenized_inputs = tokenizer(texts, truncation=True, padding="max_length", max_length=512)
        tokenized_inputs["labels"] = labels
        return tokenized_inputs

    print("Tokenizing dataset...")
    train_dataset = train_dataset.map(tokenize_and_format, batched=True, remove_columns=train_dataset.column_names)
    eval_dataset = eval_dataset.map(tokenize_and_format, batched=True, remove_columns=eval_dataset.column_names)

    model = DistilBertForSequenceClassification.from_pretrained(
        "distilbert-base-uncased", num_labels=2
    )

    def compute_metrics(pred):
        labels = pred.label_ids
        preds = np.argmax(pred.predictions, axis=1)
        precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="binary")
        acc = accuracy_score(labels, preds)
        return {"accuracy": acc, "f1": f1, "precision": precision, "recall": recall}

    training_args = TrainingArguments(
        output_dir="./results",
        num_train_epochs=1,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_metrics,
    )

    print("Starting training...")
    trainer.train()

    print("Saving model to ./model/detector_model")
    trainer.save_model("./model/detector_model")
    tokenizer.save_pretrained("./model/detector_model")
    print("Training complete!")


if __name__ == "__main__":
    train()