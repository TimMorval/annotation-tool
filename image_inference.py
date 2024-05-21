import cv2
import json
from pathlib import Path
import torch
from PIL import Image
import numpy as np
from transformers import AutoProcessor, AutoModelForTokenClassification
from torch.nn import functional as nnf
import warnings
import pandas as pd
warnings.filterwarnings("ignore")

processor = AutoProcessor.from_pretrained(
    "microsoft/layoutlmv3-base", apply_ocr=True)


file_path = "images/BENJAMIN_REPINGON_01_04_2024.png"

with open('labels.json') as f:
    label2id = json.load(f)
if Path("model").exists():
    model = AutoModelForTokenClassification.from_pretrained(
        "./model", num_labels=len(label2id))
else:
    model = AutoModelForTokenClassification.from_pretrained(
        "microsoft/layoutlmv3-base", num_labels=len(label2id)
    )

encoding = processor(
    Image.open(file_path).convert('RGB'),
    max_length=256,
    padding="max_length", truncation=True, return_tensors='pt',
    return_offsets_mapping=True
)


inputs_ids = torch.tensor(encoding['input_ids'], dtype=torch.int64).flatten()
attention_mask = torch.tensor(
    encoding['attention_mask'], dtype=torch.int64).flatten()
bbox = torch.tensor(encoding['bbox'], dtype=torch.int64).flatten(end_dim=1)
pixel_values = torch.tensor(
    encoding['pixel_values'], dtype=torch.float32).flatten(end_dim=1)

with torch.no_grad():
    op = model(input_ids=inputs_ids.unsqueeze(0),
               attention_mask=attention_mask.unsqueeze(0),
               bbox=bbox.unsqueeze(0),
               pixel_values=pixel_values.unsqueeze(0)
               )
    logits = op.logits
    predictions = logits.argmax(-1).squeeze().tolist()

    prob = nnf.softmax(logits, dim=1)
    txt = prob.squeeze().numpy()/np.sum(prob.squeeze().numpy(), axis=1).reshape(-1, 1)
    output_prob = np.max(txt, axis=1)

pred = torch.tensor(predictions)
offset_mapping = encoding['offset_mapping']
is_subword = np.array(offset_mapping.squeeze().tolist())[:, 0] != 0
true_predictions = torch.tensor(np.array(
    [pred.item() for idx, pred in enumerate(pred) if not is_subword[idx]]))

true_prob = torch.tensor(np.array([output_prob.item(
) for idx, output_prob in enumerate(output_prob) if not is_subword[idx]]))

true_boxes = torch.tensor(
    [box.tolist() for idx, box in enumerate(bbox) if not is_subword[idx]])

concat_torch = torch.column_stack((true_boxes, true_predictions, true_prob))

file_path = "images/BENJAMIN_REPINGON_01_04_2024.png"
original_image = cv2.imread(file_path)
height, width, _ = original_image.shape
image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)

with open('labels.json') as f:
    id2label = {v: k for k, v in json.load(f).items()}

font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.5
font_color = (255, 0, 0)
font_thickness = 1

factor = 1000
concat_torch[:, 0] *= width / factor  # x
concat_torch[:, 1] *= height / factor  # y
concat_torch[:, 2] *= width / factor  # width
concat_torch[:, 3] *= height / factor  # height


start = []
end = []
labels = []

for i in range(concat_torch.shape[0]):
    box, label_id, prob = concat_torch[i][:4], int(
        concat_torch[i][4]), concat_torch[i][5]
    label = id2label[label_id]
    if label == "O":
        continue
    x1, y1, x2, y2 = map(int, box)
    if x1 == x2:
        continue
    start.append((x1, y1))
    end.append((x2, y2))
    labels.append(label)

df = pd.DataFrame({'start': start, 'end': end, 'label': labels})


def process_labels(df):
    df['block'] = (df['label'].str.startswith('B')).cumsum()

    result_df = df.groupby('block').agg({
        'start': 'first',
        'end': 'last',
        'label': 'first'
    }).reset_index(drop=True)

    result_df['label'] = result_df['label'].str[2:]

    return result_df


result_df = process_labels(df)

for i, row in result_df.iterrows():
    x1, y1 = row['start']
    x2, y2 = row['end']
    label = row['label']
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    display_text = str(label)

    text_size = cv2.getTextSize(
        display_text, font, font_scale, font_thickness)[0]
    text_x = x1
    text_y = y1 - 10 if y1 - 10 > 10 else y2 + 10

    cv2.putText(image, display_text, (text_x, text_y), font,
                font_scale, font_color, font_thickness)

cv2.imwrite('annotated_image.png', cv2.cvtColor(
    image, cv2.COLOR_RGB2BGR))
