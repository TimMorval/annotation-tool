import os
import json
from collections import defaultdict


def group_files(dir_path):
    files = os.listdir(dir_path)
    files = sorted(files)

    # Dictionary to hold groups of files
    file_groups_dict = defaultdict(list)

    for file in files:
        if file.endswith(".json"):
            # Split the file name by underscores and check for a trailing number
            parts = file.split('_')
            if parts[-1].split('.')[0].isdigit():
                # If the last part before the extension is a number, remove it
                base_name = '_'.join(parts[:-1])
            else:
                # Otherwise, use the whole file name as the base name (without extension)
                base_name = file.rsplit('.', 1)[0]

            file_groups_dict[base_name].append(file)

    # Convert dictionary values to a list of lists
    file_groups = list(file_groups_dict.values())

    return file_groups


def data_fusion(dir_path, file_groups):
    for group in file_groups:
        if len(group) == 1:
            filename = group[0]
        else:
            filename = group[0].replace("_0.json", ".json")
        annotations = []
        for filename in group:
            file_path = os.path.join(dir_path, filename)
            with open(file_path) as f:
                file = json.load(f)
            data = file["predictions"][0]["result"]
            annotations.extend(data)
        yield filename, annotations


def run_test(dir_path):
    file_groups = group_files(dir_path)
    datas = data_fusion(dir_path, file_groups)
    error = 0
    for filename, annotations in datas:
        labels = set()
        for annotation in annotations:
            if annotation["type"] == "textarea":
                label = annotation["value"]["label"]
                labels.add(label)
        if "B-DATE" not in labels:
            print(f"File {filename} does not have B-DATE")
            error += 1
        if "B-TOTAL" not in labels:
            print(f"File {filename} does not have B-TOTAL")
            error += 1
    print(f"Total error: {error}")


if __name__ == "__main__":
    dir_path = "done"
    run_test(dir_path)
