import time
from pathlib import Path

import torch

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# =====================================================
# Configuration
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DB_DIR = BASE_DIR / "chroma_db"

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# =====================================================
# Embedding Model
# =====================================================

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": DEVICE},
    encode_kwargs={"normalize_embeddings": True},
)


# =====================================================
# Retriever
# =====================================================

class SpecialtyRetriever:

    def __init__(self):
        self.vectorstores = {}

    # -------------------------------------------------

    def load_collection(self, specialty):

        if specialty not in self.vectorstores:

            self.vectorstores[specialty] = Chroma(
                collection_name=specialty,
                persist_directory=DB_DIR,
                embedding_function=embeddings,
            )

        return self.vectorstores[specialty]

    # -------------------------------------------------

    def retrieve(
        self,
        question,
        specialty,
        k=6,
        fetch_k=15,
        lambda_mult=0.7,
    ):

        db = self.load_collection(specialty)

        start = time.time()

        # -------------------------------------------------
        # Step 1
        # Retrieve with MMR
        # -------------------------------------------------

        docs = db.max_marginal_relevance_search(
            query=question,
            k=k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult,
        )

        retrieval_time = time.time() - start

        # -------------------------------------------------
        # Step 2
        # Get similarity scores
        #
        # (Only for logging/evaluation)
        # -------------------------------------------------

        scored_docs = db.similarity_search_with_relevance_scores(
            query=question,
            k=k,
        )

        score_lookup = {}

        for doc, score in scored_docs:

            chunk_id = doc.metadata.get("chunk_id")

            score_lookup[chunk_id] = float(score)

        # -------------------------------------------------
        # Step 3
        # Build output
        # -------------------------------------------------

        contexts = []
        metadata = []

        for doc in docs:

            chunk_id = doc.metadata.get("chunk_id")

            contexts.append(doc.page_content)

            metadata.append({

                "chunk_id":
                chunk_id,

                "source_file":
                doc.metadata.get("source_file"),

                "page":
                doc.metadata.get("page"),

                "specialty":
                doc.metadata.get("specialty"),

                "score":
                score_lookup.get(chunk_id),

            })

        return {

            "documents": docs,

            "contexts": contexts,

            "metadata": metadata,

            "retrieval_time": retrieval_time,

        }


# =====================================================
# Demo
# =====================================================

if __name__ == "__main__":

    retriever = SpecialtyRetriever()

    result = retriever.retrieve(

        question="What are the symptoms of heart failure?",

        specialty="cardiology",

    )

    print()

    for m in result["metadata"]:

        print(m)