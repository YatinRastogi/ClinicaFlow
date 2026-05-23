# from utils.rag import retrieve_medical_context
#
# def test_rag():
#     specialty = "cardiology"
#     query = "patient complains of severe chest pain radiating to the left arm and shortness of breath."
#     print(f"Retrieving context for {specialty} with query: {query}")
#     context = retrieve_medical_context(query, specialty)
#     print("\n--- Retrieved Context ---")
#     print(context)
#     print("-------------------------\n")
#
# if __name__ == "__main__":
#     test_rag()


# test_rag.py
from utils.rag import retrieve_medical_context


def run_retrieval_eval():
    # Define a few mock patient scenarios with extracted facts
    test_cases = [
        {
            "scenario": "Acute Coronary Syndrome",
            "specialty": "cardiology",
            "query": "crushing chest pain radiating to left arm. pain_level: 9/10, sweating: yes, duration: 45 minutes"
        },
        {
            "scenario": "Routine Viral Infection",
            "specialty": "general_medicine",
            "query": "high fever, body aches, and chills. fever_duration: 3 days, temperature: 102.5F"
        },
        {
            "scenario": "Edge Case - Vague Symptoms",
            "specialty": "cardiology",
            "query": "feeling tired and sometimes my chest flutters. age: 65, history: hypertension"
        }
    ]

    for i, tc in enumerate(test_cases):
        print(f"\n{'=' * 40}")
        print(f"🧪 TEST {i + 1}: {tc['scenario']} ({tc['specialty'].upper()})")
        print(f"Query: {tc['query']}")
        print(f"{'=' * 40}")

        # Call your existing function
        context = retrieve_medical_context(tc['query'], tc['specialty'])

        # Print the first 800 characters to verify relevance quickly
        print("\n--- Top Retrieved Context ---")
        print(f"{context[:800]}...\n")


if __name__ == "__main__":
    run_retrieval_eval()