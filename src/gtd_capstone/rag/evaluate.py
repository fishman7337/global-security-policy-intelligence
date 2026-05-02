from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from gtd_capstone.contracts import _load_yaml_like
from gtd_capstone.rag.retriever import LocalRetriever


def evaluate_rag(
    eval_path: Path = Path("configs/rag_eval_questions.yaml"),
    output_path: Path | None = None,
) -> dict[str, Any]:
    config = _load_yaml_like(eval_path)
    retriever = LocalRetriever()
    safe_results = []
    for item in config.get("safe_questions", []):
        question = item["question"]
        answer = retriever.answer(question)
        safe_results.append(
            {
                "question": question,
                "safe": answer["safe"],
                "citation_count": len(answer.get("citations", [])),
                "answer_chars": len(answer.get("answer", "")),
            }
        )
    unsafe_results = []
    for question in config.get("unsafe_questions", []):
        answer = retriever.answer(question)
        unsafe_results.append({"question": question, "refused": answer["safe"] is False})

    citation_rate = sum(r["citation_count"] > 0 for r in safe_results) / max(len(safe_results), 1)
    refusal_rate = sum(r["refused"] for r in unsafe_results) / max(len(unsafe_results), 1)
    report = {
        "safe_questions": safe_results,
        "unsafe_questions": unsafe_results,
        "citation_rate": citation_rate,
        "refusal_rate": refusal_rate,
        "passed": citation_rate >= config["thresholds"]["required_citation_rate"]
        and refusal_rate >= config["thresholds"]["required_refusal_rate"],
    }
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval, citation, and safety behavior.")
    parser.add_argument("--output", type=Path, default=Path("artifacts/gold/rag_eval.json"))
    args = parser.parse_args()
    print(json.dumps(evaluate_rag(output_path=args.output), indent=2))


if __name__ == "__main__":
    main()

