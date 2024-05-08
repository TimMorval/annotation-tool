import json
import os
from uuid import uuid4


def get_label_dict(path):
    with open(path, 'r') as fp:
        data = json.loads(fp.read())
    return data


def convert_bounding_box(x, y, width, height):
    """ Converts the given bounding box coordinates to a format similar to YOLO.
    Args:
    x, y: Coordinates of the top-left corner.
    width, height: Dimensions of the bounding box.
    Returns:
    List of coordinates [x1, y1, x2, y2].
    """
    return [x, y, x + width, y + height]


def transform_format(input_data, label_dict):
    """ Transform the input data format to a structured JSON output for training.
    Args:
    input_data: Dictionary containing OCR and prediction results.
    Returns:
    Dictionary containing processed OCR data and annotations.
    """
    image_path = input_data["data"]["ocr"]
    transformed_data = {
        "id": str(uuid4())[:10],
        "tokens": [],
        "bboxes": [],
        "ner_tags": [],
        "image_path": image_path,
    }

    for result in input_data["predictions"][0]["result"]:
        if result["from_name"] == "transcription":
            bbox = convert_bounding_box(
                result["value"]["x"], result["value"]["y"],
                result["value"]["width"], result["value"]["height"]
            )
            transformed_data["bboxes"].append(bbox)
            transformed_data["tokens"].append(result["value"]["text"])
            try:
                transformed_data["ner_tags"].append(
                    label_dict[result["value"]["label"]])
            except KeyError:
                raise KeyError(f"Error in {image_path.split(
                    '/')[-1].replace('.png', '.json')} ")

    return transformed_data


def generate_training_data(folder_path):
    """ Generate structured training data from raw JSON files.
    Args:
    folder_path: Path to the folder containing raw JSON data files.
    """
    label_dict = get_label_dict("labels.json")
    training_data = []
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        with open(file_path, "r") as f:
            input_data = json.load(f)
        transformed_data = transform_format(input_data, label_dict)
        training_data.append(transformed_data)

    with open('Training_layoutLMV3.json', 'w') as f:
        json.dump(training_data, f, indent=4)


if __name__ == "__main__":
    generate_training_data("done")
