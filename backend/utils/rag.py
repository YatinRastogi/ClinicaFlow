# utils/rag.py
import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# 1. Initialize the exact same free embedding model we used to build the DB
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
DB_DIR = "./chroma_db"

def get_retriever_for_specialty(specialty: str):
    """
    Connects to the specific ChromaDB collection for the routed department.
    """
    if specialty not in ["cardiology", "general_medicine"]:
        print(f"⚠️ Warning: Unknown specialty '{specialty}'. Defaulting to general_medicine.")
        specialty = "general_medicine"

    vectorstore = Chroma(
        collection_name=specialty,
        embedding_function=embeddings,
        persist_directory=DB_DIR
    )

    # UPDATED: Fetch the top 7 most relevant chunks
    return vectorstore.as_retriever(search_kwargs={"k": 5})


def retrieve_medical_context(symptoms: str, specialty: str) -> str:
    """
    Takes the patient's symptoms, searches the relevant database,
    and formats the results into a string for the LLM prompt.
    """
    print(f"--- 🔍 Searching {specialty} guidelines for: '{symptoms}' ---")

    try:
        retriever = get_retriever_for_specialty(specialty)
        docs = retriever.invoke(symptoms)

        if not docs:
            return "No specific guidelines retrieved."

        # Format the retrieved documents into a clean string to inject into the prompt
        context_parts = []
        for i, doc in enumerate(docs):
            context_parts.append(f"Guideline Excerpt {i + 1}:\n{doc.page_content}")

        final_context = "\n\n".join(context_parts)
        print("--- ✅ Retrieval Successful ---")
        return final_context

    except Exception as e:
        print(f"--- ❌ RAG Retrieval Error: {e} ---")
        return "Standard medical guidelines apply. (Error retrieving context)"