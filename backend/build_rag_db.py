# build_rag_db.py
import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configuration
DB_DIR = "./chroma_db"
DATA_DIRS = {
    "cardiology": "data/cardiology",
    "general_medicine": "data/general_medicine"
}


def build_database():
    print("--- 🧠 Loading Embedding Model (This may take a moment on first run) ---")
    # Using a free, fast, high-quality local embedding model
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # This breaks the PDFs into readable paragraphs (1000 characters)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,  # Overlap prevents cutting a sentence in half
        add_start_index=True
    )

    for specialty, folder_path in DATA_DIRS.items():
        print(f"\n--- 📂 Processing Specialty: {specialty.upper()} ---")

        if not os.path.exists(folder_path):
            print(f"❌ Directory not found: {folder_path}. Please make sure your PDFs are there.")
            continue

        # 1. Load all PDFs from the directory
        loader = PyPDFDirectoryLoader(folder_path)
        docs = loader.load()

        if not docs:
            print(f"⚠️ No PDFs found in {folder_path}. Skipping...")
            continue

        print(f"✅ Loaded {len(docs)} pages from {specialty} PDFs.")

        # 2. Split pages into chunks
        chunks = text_splitter.split_documents(docs)
        print(f"✅ Split into {len(chunks)} searchable chunks.")

        # 3. Create or update the Chroma Vector Database Collection
        print(f"💾 Saving to ChromaDB collection: '{specialty}'...")
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=specialty,
            persist_directory=DB_DIR
        )
        print(f"🎉 {specialty.upper()} database built successfully!")


if __name__ == "__main__":
    # Ensure your directories exist
    os.makedirs("data/cardiology", exist_ok=True)
    os.makedirs("data/general_medicine", exist_ok=True)

    print("🚀 Starting RAG Database Builder...")
    build_database()