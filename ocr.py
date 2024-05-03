import json
import pytesseract
from PIL import Image
from uuid import uuid4
import os
from tqdm import tqdm


# tesseract output levels for the level of detail for the bounding boxes
LEVELS = {
    'page_num': 1,
    'block_num': 2,
    'par_num': 3,
    'line_num': 4,
    'word_num': 5
}


def convert_to_ls(image, tesseract_output):
    """
    :param image: PIL image object
    :param tesseract_output: the output from tesseract
    :param per_level: control the granularity of bboxes from tesseract
    :return: tasks.json ready to be imported into Label Studio with "Optical Character Recognition" template
    """
    image_width, image_height = image.size
    per_level_idx = LEVELS['word_num']
    results = []
    all_scores = []
    for i, level_idx in enumerate(tesseract_output['level']):
        if level_idx == per_level_idx:
            bbox = {
                'x': 100 * tesseract_output['left'][i] / image_width,
                'y': 100 * tesseract_output['top'][i] / image_height,
                'width': 100 * tesseract_output['width'][i] / image_width,
                'height': 100 * tesseract_output['height'][i] / image_height,
                'rotation': 0
            }
            text = tesseract_output['text'][i]
            label = 'O'
            if not text:
                continue
            region_id = str(uuid4())[:10]
            score = tesseract_output['conf'][i]
            bbox_result = {
                'id': region_id, 'from_name': 'bbox', 'to_name': 'image', 'type': 'rectangle',
                'value': bbox}
            transcription_result = {
                'id': region_id, 'from_name': 'transcription', 'to_name': 'image', 'type': 'textarea',
                'value': dict(text=text, label=label, **bbox), 'score': score}
            results.extend([bbox_result, transcription_result])
            all_scores.append(score)

    return {
        'data': {
            'ocr': image.filename
        },
        'predictions': [{
            'result': results,
            'score': sum(all_scores) / len(all_scores) if all_scores else 0
        }]
    }


def extract_text_from_images(image_folder):
    # Path to the folder where the images are stored
    image_files = [f for f in os.listdir(image_folder) if f.endswith('.png')]

    tasks = []

    # Progress bar with tqdm
    for file_name in tqdm(image_files, desc="Processing images"):
        file_path = os.path.join(image_folder, file_name)
        with Image.open(file_path) as image:
            tesseract_output = pytesseract.image_to_data(
                image, lang='fra', output_type=pytesseract.Output.DICT)
            task = convert_to_ls(image, tesseract_output)
            tasks.append(task)

    # create a file to import into Label Studio
    with open('ocr_tasks.json', mode='w') as f:
        json.dump(tasks, f, indent=2)


if __name__ == "__main__":
    extract_text_from_images("images")
