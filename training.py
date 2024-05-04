import torch.optim as optim
from transformers import AutoModelForTokenClassification
from torch.utils.data import DataLoader
from transformers import AutoProcessor
import torch
from load_dataset import load_training_dataset
from PIL import Image
import json
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")

# Load and process the entire dataset


def convert_to_images(image_paths):
    return [Image.open(image_path).convert("RGB") for image_path in image_paths]


def process_data_to_model_inputs(example):
    processor = AutoProcessor.from_pretrained(
        "microsoft/layoutlmv3-base", apply_ocr=False)
    encoding = processor(convert_to_images(example['image_path']), example['tokens'], boxes=example['bboxes'],
                         word_labels=example['ner_tags'], return_tensors="pt", padding=True, truncation=True)
    return {k: v.squeeze() for k, v in encoding.items()}


def train_model(model, train_loader, optimizer, device, num_epochs):
    model.train()
    model.to(device)
    for epoch in range(num_epochs):  # Loop over the dataset multiple times
        running_loss = 0.0
        # Wrap your DataLoader with tqdm for a progress bar
        progress_bar = tqdm(enumerate(train_loader), total=len(train_loader))
        for i, batch in progress_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            bbox = batch['bbox'].to(device)
            labels = batch['labels'].to(device)

            # Zero the parameter gradients
            optimizer.zero_grad()

            # Forward + backward + optimize
            outputs = model(input_ids, attention_mask=attention_mask,
                            bbox=bbox, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()

            # Print statistics
            running_loss += loss.item()
            # Update tqdm with loss information
            progress_bar.set_description(
                f"Epoch {epoch + 1} Loss: {running_loss / (i + 1):.4f}")
    print('Finished Training')


if __name__ == "__main__":

    with open('labels.json') as f:
        labels = json.load(f)

    model = AutoModelForTokenClassification.from_pretrained(
        "microsoft/layoutlmv3-base", num_labels=len(labels)
    )
    with open("Training_layoutLMV3.json") as f:
        training_data = json.load(f)

    dataset = load_training_dataset(training_data, labels)
    dataset = dataset.map(process_data_to_model_inputs, batched=True)
    dataset.set_format(type='torch', columns=[
        'input_ids', 'attention_mask', 'bbox', 'labels'])

    train_loader = DataLoader(dataset, batch_size=4, shuffle=True)
    optimizer = optim.AdamW(model.parameters(), lr=5e-5)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_model(model, train_loader, optimizer, device, num_epochs=3)

    model.save_pretrained('./model')
