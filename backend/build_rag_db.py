import os
import shutil
import uuid
import torch

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# =====================================================
# Configuration
# =====================================================

DB_DIR = "./chroma_db"

DATA_DIRS = {
    "cardiology": "data/cardiology",
    "critical_care": "data/critical_care",
    "dermatology": "data/dermatology",
    "endocrinology": "data/endocrinology",
    "gastroenterology": "data/gastroenterology",
    "neurology": "data/neurology",
    "pharmacology": "data/pharmacology",
    "pulmonology": "data/pulmonology",
}

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 300

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# =====================================================
# Build Database
# =====================================================

def build_database():

    print("=" * 70)
    print("Building ClinicaFlow Knowledge Base")
    print("=" * 70)
    print(f"Embedding Model : {EMBEDDING_MODEL}")
    print(f"Device          : {DEVICE}")
    print(f"Chunk Size      : {CHUNK_SIZE}")
    print(f"Chunk Overlap   : {CHUNK_OVERLAP}")
    print("=" * 70)

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": DEVICE},
        encode_kwargs={"normalize_embeddings": True},
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
    )

    # Remove old database
    if os.path.exists(DB_DIR):
        print("\nRemoving previous Chroma database...")
        shutil.rmtree(DB_DIR)

    total_pages = 0
    total_chunks = 0

    # =================================================

    for specialty, folder in DATA_DIRS.items():

        print("\n" + "=" * 70)
        print(f"Processing {specialty.upper()}")
        print("=" * 70)

        if not os.path.exists(folder):
            print(f"Folder not found: {folder}")
            continue

        loader = PyPDFDirectoryLoader(folder)
        documents = loader.load()

        if len(documents) == 0:
            print("No PDFs found.")
            continue

        print(f"Pages Loaded : {len(documents)}")

        chunks = splitter.split_documents(documents)

        print(f"Chunks Created : {len(chunks)}")

        # --------------------------------------------
        # Add Metadata
        # --------------------------------------------

        for chunk in chunks:

            source = os.path.basename(
                chunk.metadata.get("source", "")
            )

            chunk.metadata["specialty"] = specialty
            chunk.metadata["source_file"] = source
            chunk.metadata["page"] = chunk.metadata.get("page", -1)
            chunk.metadata["chunk_id"] = str(uuid.uuid4())

        # --------------------------------------------
        # Chunk Statistics
        # --------------------------------------------

        chunk_lengths = [
            len(chunk.page_content)
            for chunk in chunks
        ]

        print(f"Average Chunk Length : {sum(chunk_lengths)//len(chunk_lengths)}")
        print(f"Smallest Chunk       : {min(chunk_lengths)}")
        print(f"Largest Chunk        : {max(chunk_lengths)}")

        # --------------------------------------------
        # Save Collection
        # --------------------------------------------

        print("Saving to ChromaDB...")

        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,  
            collection_name=specialty,
            persist_directory=DB_DIR,
        )

        print(f"{specialty.upper()} collection completed.")

        total_pages += len(documents)
        total_chunks += len(chunks)

    # =================================================

    print("\n" + "=" * 70)
    print("Database Build Complete")
    print("=" * 70)

    print(f"Total Pages Indexed  : {total_pages}")
    print(f"Total Chunks Indexed : {total_chunks}")
    print(f"Database Location    : {DB_DIR}")

    print("=" * 70)


# =====================================================
# Main
# =====================================================

if __name__ == "__main__":

    # Create all required folders automatically

    for folder in DATA_DIRS.values():
        os.makedirs(folder, exist_ok=True)

    build_database()