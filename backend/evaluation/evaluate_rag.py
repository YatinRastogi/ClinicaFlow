import os
import json
import sys
from datetime import datetime
from pathlib import Path

from datasets import Dataset

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]

for path in (PROJECT_ROOT, BACKEND_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from retriever import SpecialtyRetriever
from generator import MedicalGenerator
from test_cases import TEST_CASES


# ============================================================
# Output Directory
# ============================================================

OUTPUT_DIR = "outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# Initialize Components
# ============================================================

retriever = SpecialtyRetriever()

generator = MedicalGenerator()


# ============================================================
# Build Evaluation Dataset
# ============================================================

def build_dataset():

    evaluation_rows = []

    retrieval_logs = []

    retrieval_times = []

    generation_times = []

    total_cases = len(TEST_CASES)

    print("=" * 70)
    print("Running ClinicaFlow Evaluation")
    print("=" * 70)

    for idx, case in enumerate(TEST_CASES, start=1):

        print(f"[{idx}/{total_cases}] {case['specialty']}")

        # ---------------------------------------------

        retrieval = retriever.retrieve(

            question=case["question"],

            specialty=case["specialty"],

        )

        # ---------------------------------------------

        generation = generator.generate(

            question=case["question"],

            contexts=retrieval["contexts"],

        )

        # ---------------------------------------------

        retrieval_times.append(

            retrieval["retrieval_time"]

        )

        generation_times.append(

            generation["generation_time"]

        )

        # ---------------------------------------------

        evaluation_rows.append(
            {
                "question": case["question"],
                "answer": generation["answer"],
                "ground_truth": case["reference_answer"],
                "contexts": retrieval["contexts"],
            }
        )

        # ---------------------------------------------

        retrieval_logs.append(
            {
                "id": case["id"],
                "specialty": case["specialty"],
                "question": case["question"],
                "ground_truth": case["reference_answer"],
                "answer": generation["answer"],
                "retrieval_time": retrieval["retrieval_time"],
                "generation_time": generation["generation_time"],
                "retrieved_chunks": retrieval["metadata"],
            }
        )

    dataset = Dataset.from_list(evaluation_rows)

    return (

        dataset,

        retrieval_logs,

        retrieval_times,

        generation_times,

    )

# ============================================================
# Imports
# ============================================================

import pandas as pd

from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper

from metrics import get_metrics, ragas_llm
from retriever import embeddings


# ============================================================
# Run RAGAS
# ============================================================

def run_ragas(dataset):

    print()
    print("=" * 70)
    print("Running RAGAS Evaluation...")
    print("=" * 70)

    result = evaluate(
        dataset=dataset,
        metrics=get_metrics(),
        llm=ragas_llm,
        embeddings=LangchainEmbeddingsWrapper(embeddings),
        column_map={
            "user_input": "question",
            "response": "answer",
            "retrieved_contexts": "contexts",
            "reference": "ground_truth",
        },
    )

    return result


# ============================================================
# Save Results
# ============================================================

def save_outputs(
    result,
    retrieval_logs,
    retrieval_times,
    generation_times,
):

    # --------------------------------------------------------

    df = result.to_pandas()

    csv_path = os.path.join(
        OUTPUT_DIR,
        "results.csv",
    )

    df.to_csv(
        csv_path,
        index=False,
    )

    # --------------------------------------------------------
    # JSON Results
    # --------------------------------------------------------

    json_path = os.path.join(
        OUTPUT_DIR,
        "evaluation_results.json",
    )

    with open(
        json_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            result.scores,
            f,
            indent=4,
        )

    # --------------------------------------------------------
    # Retrieval Logs
    # --------------------------------------------------------

    retrieval_path = os.path.join(
        OUTPUT_DIR,
        "retrieved_chunks.json",
    )

    with open(
        retrieval_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            retrieval_logs,
            f,
            indent=4,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary_path = os.path.join(
        OUTPUT_DIR,
        "summary.txt",
    )

    avg_retrieval = (
        sum(retrieval_times)
        / len(retrieval_times)
    )

    avg_generation = (
        sum(generation_times)
        / len(generation_times)
    )

    total_time = (
        avg_retrieval
        + avg_generation
    )

    with open(
        summary_path,
        "w",
        encoding="utf-8",
    ) as f:

        f.write("=" * 60 + "\n")

        f.write(
            "ClinicaFlow RAG Evaluation Summary\n"
        )

        f.write("=" * 60 + "\n\n")

        f.write(
            f"Generated : {datetime.now()}\n\n"
        )

        f.write(
            f"Total Test Cases : {len(TEST_CASES)}\n\n"
        )

        # -----------------------------

        for metric in df.columns:

            value = df[metric].mean()

            f.write(
                f"{metric:25s}: {value:.4f}\n"
            )

        f.write("\n")

        f.write(
            f"Average Retrieval Time : {avg_retrieval:.3f} sec\n"
        )

        f.write(
            f"Average Generation Time : {avg_generation:.3f} sec\n"
        )

        f.write(
            f"Average Total Time : {total_time:.3f} sec\n"
        )

    print()
    print("=" * 70)
    print("Evaluation Complete")
    print("=" * 70)

    print()

    print(df)

    print()

    print(f"CSV Saved : {csv_path}")

    print(f"JSON Saved : {json_path}")

    print(f"Logs Saved : {retrieval_path}")

    print(f"Summary Saved : {summary_path}")


# ============================================================
# Main
# ============================================================

def main():

    (
        dataset,
        retrieval_logs,
        retrieval_times,
        generation_times,
    ) = build_dataset()

    result = run_ragas(dataset)

    save_outputs(
        result,
        retrieval_logs,
        retrieval_times,
        generation_times,
    )


# ============================================================

if __name__ == "__main__":

    main()