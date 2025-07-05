
import json
import os

def save_checkpoint(processed_urls, checkpoint_file="checkpoint.json"):
    with open(checkpoint_file, 'w') as f:
        json.dump({"processed": list(processed_urls)}, f)

def load_checkpoint(checkpoint_file="checkpoint.json"):
    if not os.path.exists(checkpoint_file):
        return set()
    try:
        with open(checkpoint_file, 'r') as f:
            return set(json.load(f).get("processed", []))
    except Exception:
        return set()
