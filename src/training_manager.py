import json
import random
import sys
from pathlib import Path

class TrainingManager:
    def __init__(self):
        self.data_file = Path(__file__).parent.parent / 'data' / 'training_data.json'
        self.load_data()

    def load_data(self):
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {"math_problems": [], "conversations": []}
            self.save_data()

    def save_data(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=4)

    def add_training_item(self, category, item):
        if category in self.data:
            self.data[category].append(item)
            self.save_data()
            return True
        return False

    def get_response(self, input_text):
        input_text = input_text.lower().strip()
        # Check conversations and their variations
        for conv in self.data["conversations"]:
            if input_text == conv["input"].lower() or \
               any(variation.lower() in input_text for variation in conv.get("variations", [])):
                return random.choice(conv["responses"])
        return None

    def add_variation(self, category, input_text, variation):
        for item in self.data[category]:
            if item["input"].lower() == input_text.lower():
                if "variations" not in item:
                    item["variations"] = []
                if variation.lower() not in [v.lower() for v in item["variations"]]:
                    item["variations"].append(variation)
                    self.save_data()
                    return True
        return False

    def add_response(self, input_text, new_response):
        for conv in self.data["conversations"]:
            if conv["input"] == input_text:
                conv["responses"].append(new_response)
                self.save_data()
                return True
        return False

    def get_math_problems(self):
        return json.dumps(self.data["math_problems"])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No command provided", file=sys.stderr)
        sys.exit(1)

    manager = TrainingManager()
    command = sys.argv[1]

    if command == "get_math_problems":
        print(manager.get_math_problems())
    elif command == "add":
        if len(sys.argv) < 4:
            print("Missing category or item", file=sys.stderr)
            sys.exit(1)
        category = sys.argv[2]
        item = json.loads(sys.argv[3])
        manager.add_training_item(category, item)
    # ...handle other commands here later...
