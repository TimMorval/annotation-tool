import json
from pathlib import Path


# Load the JSON data from a file rather than a string.
with open("ocr_tasks.json", "r") as file:
    tasks = json.load(file)

# Ensure you manage file opening and closing correctly using a context manager.
for task in tasks:
    basename = Path(task["data"]["ocr"]).stem
    with open(f"predictions/{basename}.json", "w") as f:
        json.dump(task, f)
