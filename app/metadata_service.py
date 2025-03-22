import json
import os

# Путь к файлу, в котором храним соответствие хешей и имен
metadata_file = "metadata.json"


def load_metadata():
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            return json.load(f)
    return {}


def save_metadata(metadata):
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=4)


