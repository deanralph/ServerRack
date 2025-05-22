import json
import os

# Path to the JSON file
JSON_FILE_PATH = 'nodes.json'

def load_json(file_path):
    """Load JSON data from a file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}

def save_json(file_path, data):
    """Save JSON data to a file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def get_or_create_node(node_name):
    """Retrieve or create a node entry."""
    data = load_json(JSON_FILE_PATH)
    
    # Search for the node
    for entry in data.get("nodes", []):
        if entry.get("node") == node_name:
            return entry
    
    # If not found, create a new entry
    new_entry = {"node": node_name, "ip": "TempIndex", "logo": "TempIndex", "status": "TempIndex", "softname": "TempIndex"}
    if "nodes" not in data:
        data["nodes"] = []
    data["nodes"].append(new_entry)
    save_json(JSON_FILE_PATH, data)
    return new_entry

# Example usage
if __name__ == "__main__":
    node_name = input("Enter the node name: ")
    result = get_or_create_node(node_name)
    print(result)