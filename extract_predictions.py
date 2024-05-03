import json
from pathlib import Path


def extract_predictions(tasks_json_path):
    # Load the JSON data from a file rather than a string.
    with open(tasks_json_path, "r") as file:
        tasks = json.load(file)

    if not Path("predictions").exists():
        Path("predictions").mkdir()

    # Ensure you manage file opening and closing correctly using a context manager.
    for task in tasks:
        basename = Path(task["data"]["ocr"]).stem
        with open(f"predictions/{basename}.json", "w") as f:
            json.dump(task, f)


if __name__ == "__main__":
    extract_predictions("ocr_tasks.json")
