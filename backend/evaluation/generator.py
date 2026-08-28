import time

from langchain_core.prompts import ChatPromptTemplate

# ---------------------------------------------------------
# Import your ClinicaFlow LLM
# ---------------------------------------------------------

# Change this import according to your project
# Example:
#
# from backend.utils.llm import llm
#
# or
#
# from backend.llm import llm
#
# ------------------------------

try:
    from backend.utils.llm import llm
except ModuleNotFoundError:  # pragma: no cover - fallback for direct script execution
    from utils.llm import llm


# =========================================================
# Prompt
# =========================================================

SYSTEM_PROMPT = """
You are ClinicaFlow, an AI Clinical Decision Support Assistant.

Answer ONLY using the retrieved medical context.

Rules:

1. Never use outside knowledge.

2. If the answer is not present in the retrieved context,
reply exactly:

"I don't have enough information from the retrieved documents."

3. Do not invent diseases.

4. Do not invent treatments.

5. Mention investigations whenever appropriate.

6. Mention emergency red flags whenever applicable.

7. Keep answers concise.

8. Use professional medical language.
"""


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            """
Question:

{question}

Retrieved Context:

{context}
            """,
        ),
    ]
)

chain = prompt | llm


# =========================================================
# Generator
# =========================================================

class MedicalGenerator:

    def __init__(self):
        self.chain = chain

    def generate(
        self,
        question,
        contexts,
    ):

        context_text = "\n\n".join(contexts)

        start = time.time()

        response = self.chain.invoke(
            {
                "question": question,
                "context": context_text,
            }
        )

        generation_time = time.time() - start

        return {
            "answer": response.content,
            "generation_time": generation_time,
        }


# =========================================================
# Example
# =========================================================

if __name__ == "__main__":

    generator = MedicalGenerator()

    contexts = [
        """
Heart failure is characterized by dyspnea,
fatigue and fluid retention.

BNP and Echocardiography are useful investigations.
"""
    ]

    result = generator.generate(
        question="What investigations are useful in heart failure?",
        contexts=contexts,
    )

    print(result["answer"])

    print()

    print("Generation Time:", result["generation_time"])