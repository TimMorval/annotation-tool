import os
import json
import cv2
import torch
import warnings
import numpy as np
import pandas as pd
import pytesseract
from PIL import Image
from pathlib import Path
from transformers import AutoProcessor, AutoModelForTokenClassification
from torch.nn import functional as nnf

os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore")


class ImageAnnotator:
    def __init__(self, model_path="model", labels_path="labels.json", margin=5):
        self.model, self.label2id = self.load_model_and_labels(
            model_path, labels_path)
        self.processor = AutoProcessor.from_pretrained(
            "microsoft/layoutlmv3-base", apply_ocr=True)
        self.id2label = {v: k for k, v in self.label2id.items()}
        self.margin = margin

    def load_model_and_labels(self, model_path, labels_path):
        with open(labels_path) as f:
            label2id = json.load(f)
        if Path(model_path).exists():
            model = AutoModelForTokenClassification.from_pretrained(
                model_path, num_labels=len(label2id))
        else:
            model = AutoModelForTokenClassification.from_pretrained(
                "microsoft/layoutlmv3-base", num_labels=len(label2id))
        return model, label2id

    def get_predictions(self, file_path):
        image = Image.open(file_path).convert('RGB')
        encoding = self.processor(image, max_length=256, padding="max_length",
                                  truncation=True, return_tensors='pt', return_offsets_mapping=True)

        with torch.no_grad():
            op = self.model(
                input_ids=encoding['input_ids'],
                attention_mask=encoding['attention_mask'],
                bbox=encoding['bbox'],
                pixel_values=encoding['pixel_values']
            )
        return encoding, op.logits

    def process_logits(self, logits, encoding, width, height):
        predictions = logits.argmax(-1).squeeze().tolist()
        prob = nnf.softmax(logits, dim=1)
        output_prob = np.max(prob.squeeze().numpy(), axis=1)

        offset_mapping = encoding['offset_mapping'].squeeze().tolist()
        is_subword = np.array([offset[0] != 0 for offset in offset_mapping])

        true_predictions = [pred for idx, pred in enumerate(
            predictions) if not is_subword[idx]]
        true_boxes = [box for idx, box in enumerate(
            encoding['bbox'].squeeze().tolist()) if not is_subword[idx]]
        true_prob = [prob for idx, prob in enumerate(
            output_prob) if not is_subword[idx]]

        true_boxes = np.array(true_boxes)
        true_boxes[:, [0, 2]] = true_boxes[:, [0, 2]] * width / 1000
        true_boxes[:, [1, 3]] = true_boxes[:, [1, 3]] * height / 1000

        return true_boxes, true_predictions, true_prob

    def create_dataframe(self, true_boxes, true_predictions, true_prob):
        data = []
        for box, label_id, prob in zip(true_boxes, true_predictions, true_prob):
            label = self.id2label[int(label_id)]
            if label != "O" and box[0] != box[2]:
                data.append({
                    'start': (int(box[0]), int(box[1])),
                    'end': (int(box[2]), int(box[3])),
                    'label': label
                })
            if data == []:
                raise ValueError("No labels detected in the image")
        return pd.DataFrame(data)

    def process_labels(self, df):
        df['block'] = (df['label'].str.startswith('B')).cumsum()
        result_df = df.groupby('block').agg({
            'start': 'first',
            'end': 'last',
            'label': 'first'
        }).reset_index(drop=True)
        result_df['label'] = result_df['label'].str[2:]
        return result_df

    def annotate_image(self, image_path, result_df, save_path=None):
        result_dict = {}
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_color = (255, 0, 0)
        font_thickness = 1

        for _, row in result_df.iterrows():
            x1, y1 = row['start']
            x2, y2 = row['end']
            label = row['label']
            roi = image[max(0, y1-self.margin): min(image.shape[0], y2+self.margin),
                        max(0, x1-self.margin): min(image.shape[1], x2+self.margin)]
            ocr_text = pytesseract.image_to_string(
                roi, lang='fra').replace('\n', ' ').strip()

            if label in result_dict:
                result_dict[label].append(ocr_text)
            else:
                result_dict[label] = [ocr_text]

            if save_path:
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                display_text = f"{ocr_text} ({label})"
                text_x = x1
                text_y = y1 - 10 if y1 - 10 > 10 else y2 + 10
                cv2.putText(image, display_text, (text_x, text_y),
                            font, font_scale, font_color, font_thickness)

        if save_path:
            cv2.imwrite(save_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))

        return result_dict

    def get_formatted_predictions(self, file_path):
        original_image = cv2.imread(file_path)
        if original_image is None:
            raise FileNotFoundError("Image not found")
        height, width, _ = original_image.shape
        encoding, logits = self.get_predictions(file_path)
        true_boxes, true_predictions, true_prob = self.process_logits(
            logits, encoding, width, height)
        return true_boxes, true_predictions, true_prob

    def get_processed_dataframe(self, true_boxes, true_predictions, true_prob):
        df = self.create_dataframe(true_boxes, true_predictions, true_prob)
        result_df = self.process_labels(df)
        return result_df

    def run(self, file_path, save_path=None):
        true_boxes, true_predictions, true_prob = self.get_formatted_predictions(
            file_path)
        df = self.get_processed_dataframe(
            true_boxes, true_predictions, true_prob)
        result_dict = self.annotate_image(
            file_path, df, save_path=save_path)
        return result_dict


if __name__ == "__main__":
    annotator = ImageAnnotator()
    image_path = input("Enter the image path: ")
    result_dict = annotator.run(image_path,
                                save_path="annotated_image.png")
    print(result_dict)
