import json
import os
from Inference import ImageAnnotator
from tqdm import tqdm

annotator = ImageAnnotator()
if not os.path.exists("results"):
    os.mkdir("results")

errors = []
for image in tqdm(os.listdir("images"), desc="Annotating images"):
    if image.endswith(".png"):
        if os.path.exists(f"results/{image.replace('.png', '.json')}"):
            continue
        try:
            result_dict = annotator.run(f"images/{image}")
            with open(f"results/{image.replace(".png", ".json")}", mode='w') as f:
                json.dump(result_dict, f, indent=2)
        except Exception as e:
            errors.append(f"Error processing {image}: {e}")
            continue
for error in errors:
    print(error)
print(f"Total errors: {len(errors)}")
