import os
from unidecode import unidecode
import json


def withdraw_spec(dir_path):
    for file in os.listdir(dir_path):
        new_name = unidecode(file)
        os.rename(os.path.join(dir_path, file),
                  os.path.join(dir_path, new_name))


def change_image_path(file_path):
    res = []
    with open(file_path, 'r') as f:
        datas = json.load(f)
    for data in datas:
        data['image_path'] = unidecode(data['image_path'])
        res.append(data)
    with open(file_path, 'w') as f:
        json.dump(res, f)


if __name__ == "__main__":
    change_image_path("Training_layoutLMV3.json")
