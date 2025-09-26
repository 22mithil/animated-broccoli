import os
import json
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer("BAAI/bge-large-en-v1.5")

# Input and output folders
GRAPH_DIR = "graphs"
OUTPUT_DIR = "embeded_graphs"

# Make sure output folder exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_embedding(text):
    """Generate embedding for a given text."""
    if not text or not text.strip():
        return []
    return model.encode(text).tolist()

def process_file(filepath, outdir):
    """Load JSON, add embeddings, and save updated JSON."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Movie embedding
    if "movie" in data:
        movie = data["movie"]
        text = f"{movie.get('title','')} {movie.get('plot_summary','')} {' '.join(movie.get('themes', []))}"
        movie["embedding"] = get_embedding(text)

    # Characters embedding
    if "characters" in data:
        for char in data["characters"]:
            text = f"{char.get('name','')} {char.get('role','')} {char.get('archetype','')} {char.get('description','')}"
            char["embedding"] = get_embedding(text)

    # Scenes embedding
    if "scenes" in data:
        for scene in data["scenes"]:
            text = scene.get("summary", "")
            scene["embedding"] = get_embedding(text)

    # Locations embedding
    if "locations" in data:
        for loc in data["locations"]:
            text = f"{loc.get('name','')} {loc.get('type','')} {loc.get('description','')}"
            loc["embedding"] = get_embedding(text)

    # Objects embedding
    if "objects" in data:
        for obj in data["objects"]:
            text = f"{obj.get('name','')} {obj.get('type','')} {obj.get('significance','')}"
            obj["embedding"] = get_embedding(text)

    # Save updated file to embeded_graphs folder
    filename = os.path.basename(filepath).replace(".json", "_with_embeddings.json")
    outpath = os.path.join(outdir, filename)

    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Processed and saved: {outpath}")

def main():
    for filename in os.listdir(GRAPH_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(GRAPH_DIR, filename)
            process_file(filepath, OUTPUT_DIR)

if __name__ == "__main__":
    main()
