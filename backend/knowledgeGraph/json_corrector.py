import os
import json

def flatten_relationships(data):
    """
    Flatten 'properties' in relationships and replace nulls with empty strings.
    """
    def replace_nulls(obj):
        if isinstance(obj, dict):
            return {k: replace_nulls(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [replace_nulls(i) for i in obj]
        elif obj is None:
            return ""
        else:
            return obj

    data = replace_nulls(data)

    for rel in data.get("relationships", []):
        props = rel.pop("properties", {})
        if isinstance(props, dict):
            for k, v in props.items():
                rel[k] = v  # flatten

    return data

def process_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    
    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            
            with open(input_path, "r", encoding="utf-8") as f:
                raw_json = json.load(f)
            
            corrected_json = flatten_relationships(raw_json)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(corrected_json, f, indent=2)
            
            print(f"✅ Corrected: {filename}")

if __name__ == "__main__":
    input_folder = "graphs"  # folder containing original JSONs
    output_folder = "corrected_graphs"  # folder to save corrected JSONs

    process_folder(input_folder, output_folder)
    print(f"All JSON files processed. Corrected files saved in '{output_folder}'")
