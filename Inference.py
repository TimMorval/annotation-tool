import numpy as np
import cv2
import json
from pathlib import Path
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForTokenClassification
import warnings
warnings.filterwarnings("ignore")


def process_image(image_path):
    processor = AutoProcessor.from_pretrained(
        "microsoft/layoutlmv3-base", apply_ocr=True)
    encoding = processor(Image.open(image_path).convert(
        'RGB'), return_tensors="pt", return_offsets_mapping=True)

    with open('labels.json') as f:
        label2id = json.load(f)

    if Path("model").exists():
        model = AutoModelForTokenClassification.from_pretrained(
            "./model", num_labels=len(label2id))
    else:
        model = AutoModelForTokenClassification.from_pretrained(
            "microsoft/layoutlmv3-base", num_labels=len(label2id))

    # Prepare tensors
    inputs_ids = torch.tensor(
        encoding['input_ids'], dtype=torch.int64).flatten()
    attention_mask = torch.tensor(
        encoding['attention_mask'], dtype=torch.int64).flatten()
    bbox = torch.tensor(encoding['bbox'], dtype=torch.int64).flatten(end_dim=1)
    pixel_values = torch.tensor(
        encoding['pixel_values'], dtype=torch.float32).flatten(end_dim=1)

    inputs = encoding['input_ids'][0]
    decoded_text = processor.decode(inputs, skip_special_tokens=True)
    words = decoded_text.split()

    id2label = {v: k for k, v in label2id.items()}

    with torch.no_grad():
        op = model(input_ids=inputs_ids.unsqueeze(0),
                   attention_mask=attention_mask.unsqueeze(0),
                   bbox=bbox.unsqueeze(0),
                   pixel_values=pixel_values.unsqueeze(0)
                   )
        logits = op.logits
        predictions = logits.argmax(-1).squeeze().tolist()

    offset_mapping = encoding['offset_mapping']
    is_subword = np.array(offset_mapping.squeeze().tolist())[:, 0] != 0
    is_empty = [box[0] == box[1] or box[2] == box[3] for box in bbox]
    true_predictions = [id2label[pred] for idx, pred in enumerate(
        predictions) if not is_subword[idx] and not is_empty[idx]]
    true_boxes = [box.tolist() for idx, box in enumerate(
        bbox) if not is_subword[idx] and not is_empty[idx]]

    image = cv2.imread(image_path)
    height, width, _ = image.shape

    for box, word, label in zip(true_boxes, words, true_predictions):
        if label != "O":
            print(label, word)


if __name__ == "__main__":
    image_path = input("Enter image path: ")
    process_image(image_path)
