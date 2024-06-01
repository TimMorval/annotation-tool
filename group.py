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

        combined_data = defaultdict(list)

        for file in group:
            file_path = os.path.join(dir_path, file)
            with open(file_path) as f:
                file_content = json.load(f)

            for key, value_list in file_content.items():
                if isinstance(value_list, list):
                    combined_data[key].extend(
                        [value for value in value_list if value != ""])

        # Convert defaultdict to regular dict for output
        combined_data = dict(combined_data)

        yield filename, combined_data


# Example usage:
dir_path = 'results'
if not os.path.exists('combined'):
    os.makedirs('combined')
file_groups = group_files(dir_path)
for filename, combined_annotations in data_fusion(dir_path, file_groups):
    with open(f'combined/{filename}', 'w') as f:
        f.write(json.dumps(combined_annotations, indent=2))
