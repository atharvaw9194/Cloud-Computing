from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for
import os
import json
from utils import encrypt, decrypt, split_file

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NODES = [
    os.path.join(BASE_DIR, "storage_nodes/node1"),
    os.path.join(BASE_DIR, "storage_nodes/node2"),
    os.path.join(BASE_DIR, "storage_nodes/node3"),
]

METADATA_FILE = os.path.join(BASE_DIR, "metadata.json")


# ---------------- METADATA ---------------- #
def load_metadata():
    if not os.path.exists(METADATA_FILE):
        return {}
    with open(METADATA_FILE, "r") as f:
        return json.load(f)


def save_metadata(data):
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------------- HOME (UI) ---------------- #
@app.route("/")
def home():
    metadata = load_metadata()
    files = list(metadata.keys())
    return render_template("index.html", files=files)


# ---------------- UPLOAD ---------------- #
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file uploaded"

    file = request.files["file"]
    filename = file.filename

    if filename == "":
        return "Empty filename"

    temp_path = os.path.join(BASE_DIR, f"temp_{filename}")
    file.save(temp_path)

    chunks = split_file(temp_path)

    metadata = load_metadata()
    metadata[filename] = []

    for i, data in chunks:
        encrypted = encrypt(data)

        node = NODES[i % len(NODES)]
        chunk_name = f"{filename}_chunk_{i}"

        chunk_path = os.path.join(node, chunk_name)

        with open(chunk_path, "wb") as f:
            f.write(encrypted)

        metadata[filename].append({
            "chunk": chunk_name,
            "node": node
        })

    save_metadata(metadata)
    os.remove(temp_path)

    return redirect(url_for("home"))


# ---------------- DOWNLOAD (API) ---------------- #
@app.route("/download/<filename>", methods=["GET"])
def download(filename):
    metadata = load_metadata()

    if filename not in metadata:
        return "File not found", 404

    output_data = b''

    for chunk_info in metadata[filename]:
        path = os.path.join(chunk_info["node"], chunk_info["chunk"])

        with open(path, "rb") as f:
            encrypted = f.read()

        output_data += decrypt(encrypted)

    output_path = os.path.join(BASE_DIR, f"downloaded_{filename}")

    with open(output_path, "wb") as f:
        f.write(output_data)

    return send_file(output_path, as_attachment=True)


# ---------------- DELETE (BONUS FEATURE) ---------------- #
@app.route("/delete/<filename>")
def delete_file(filename):
    metadata = load_metadata()

    if filename not in metadata:
        return "File not found"

    # delete chunks
    for chunk_info in metadata[filename]:
        path = os.path.join(chunk_info["node"], chunk_info["chunk"])
        if os.path.exists(path):
            os.remove(path)

    # remove metadata
    del metadata[filename]
    save_metadata(metadata)

    return redirect(url_for("home"))


# ---------------- START SERVER ---------------- #
if __name__ == "__main__":
    for node in NODES:
        os.makedirs(node, exist_ok=True)

    app.run(host="0.0.0.0", port=5900, debug=True)