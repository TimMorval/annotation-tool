from datasets import Dataset, Features, Value, ClassLabel, Sequence
import json


def load_training_dataset(data, labels):

    columns = {key: [dic[key] for dic in data] for key in data[0]}

    features = Features({
        'id': Value('string'),
        'tokens': Sequence(Value('string')),
        'bboxes': Sequence(Sequence(Value('int32'))),
        'ner_tags': Sequence(ClassLabel(names=list(labels.keys()))),
        'image_path': Value('string')
    })

    dataset = Dataset.from_dict(columns, features=features)

    return dataset


if __name__ == "__main__":
    with open("Training_layoutLMV3.json") as f:
        training_data = json.load(f)
    with open('labels.json') as f:
        labels = json.load(f)
    dataset = load_training_dataset(training_data, labels)
    print(dataset)
    print(dataset[0])  # Print the first item to check the structure
    print(dataset.features)  # Check the features of your dataset
