import streamlit as st
import os
import json
from pathlib import Path
import sys

# Add controller to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'controller'))

from utils import encrypt, decrypt, split_file

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

NODES = [
    os.path.join(BASE_DIR, "storage_nodes/node1"),
    os.path.join(BASE_DIR, "storage_nodes/node2"),
    os.path.join(BASE_DIR, "storage_nodes/node3"),
]

METADATA_FILE = os.path.join(BASE_DIR, "metadata.json")

# Ensure nodes exist
for node in NODES:
    os.makedirs(node, exist_ok=True)

# ============ METADATA FUNCTIONS ============
def load_metadata():
    if not os.path.exists(METADATA_FILE):
        return {}
    with open(METADATA_FILE, "r") as f:
        return json.load(f)

def save_metadata(data):
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ============ STREAMLIT UI ============
st.set_page_config(page_title="Cloud Storage", layout="wide")
st.title("☁️ Cloud Storage System")

# Tabs
tab1, tab2 = st.tabs(["Upload File", "Download File"])

# ============ UPLOAD TAB ============
with tab1:
    st.subheader("Upload a File")
    
    uploaded_file = st.file_uploader("Choose a file to upload")
    
    if uploaded_file is not None:
        if st.button("Upload", key="upload_btn"):
            with st.spinner("Uploading and encrypting..."):
                # Save temp file
                temp_path = os.path.join(BASE_DIR, f"temp_{uploaded_file.name}")
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Split into chunks
                chunks = split_file(temp_path)
                
                # Encrypt and distribute
                metadata = load_metadata()
                metadata[uploaded_file.name] = []
                
                for i, data in chunks:
                    encrypted = encrypt(data)
                    node = NODES[i % len(NODES)]
                    chunk_name = f"{uploaded_file.name}_chunk_{i}"
                    chunk_path = os.path.join(node, chunk_name)
                    
                    with open(chunk_path, "wb") as f:
                        f.write(encrypted)
                    
                    metadata[uploaded_file.name].append({
                        "chunk": chunk_name,
                        "node": node
                    })
                
                save_metadata(metadata)
                os.remove(temp_path)
                
                st.success(f"✅ File '{uploaded_file.name}' uploaded successfully!")
                st.info(f"📦 Chunks created: {len(chunks)}")

# ============ DOWNLOAD TAB ============
with tab2:
    st.subheader("Download a File")
    
    metadata = load_metadata()
    
    if not metadata:
        st.warning("No files available for download")
    else:
        # File selector
        filenames = list(metadata.keys())
        selected_file = st.selectbox("Select a file to download", filenames)
        
        if st.button("Download", key="download_btn"):
            with st.spinner("Decrypting and reconstructing..."):
                output_data = b''
                
                for chunk_info in metadata[selected_file]:
                    path = os.path.join(chunk_info["node"], chunk_info["chunk"])
                    
                    with open(path, "rb") as f:
                        encrypted = f.read()
                    
                    output_data += decrypt(encrypted)
                
                # Download button
                st.download_button(
                    label=f"📥 Download {selected_file}",
                    data=output_data,
                    file_name=selected_file,
                    mime="application/octet-stream"
                )

# ============ METADATA VIEW ============
st.divider()
st.subheader("📊 Storage Metadata")

metadata = load_metadata()
if metadata:
    for filename, chunks in metadata.items():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text(f"📄 {filename}")
        with col2:
            st.text(f"Chunks: {len(chunks)}")
        with col3:
            if st.button("Delete", key=f"del_{filename}"):
                # Delete chunks
                for chunk_info in chunks:
                    try:
                        os.remove(os.path.join(chunk_info["node"], chunk_info["chunk"]))
                    except:
                        pass
                # Update metadata
                del metadata[filename]
                save_metadata(metadata)
                st.rerun()
else:
    st.info("No files stored yet")
