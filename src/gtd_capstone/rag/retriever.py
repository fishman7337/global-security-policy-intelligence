from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from gtd_capstone.safety import REFUSAL, is_unsafe_request


@dataclass
class DocumentChunk:
    id: str
    title: str
    text: str
    source: str


def default_corpus(root: Path | None = None) -> list[DocumentChunk]:
    root = root or Path.cwd()
    docs: list[DocumentChunk] = [
        DocumentChunk(
            id="ethics-policy",
            title="Ethics Policy",
            source="docs/ethics.md",
            text=(
                "This project supports aggregate historical analysis only. It refuses tactical, "
                "targeting, weaponization, evasion, or operational guidance."
            ),
        ),
        DocumentChunk(
            id="complexity",
            title="Complexity Report",
            source="docs/complexity.md",
            text=(
                "The capstone documents O(n) hash aggregation, O(V+E) BFS, "
                "O((V+E) log V) Dijkstra, O(iterations*E) PageRank, and vector retrieval tradeoffs."
            ),
        ),
        DocumentChunk(
            id="methodology",
            title="Methodology",
            source="docs/methodology.md",
            text=(
                "The data pipeline uses bronze, silver, and gold layers. Raw Excel files are converted "
                "to Parquet, cleaned, validated, and transformed into dashboard, model, graph, and RAG assets."
            ),
        ),
        DocumentChunk(
            id="wandb",
            title="Weights & Biases Tracking",
            source="docs/methodology.md",
            text=(
                "W&B tracks metrics, hyperparameters, confusion matrices, artifacts, datasets, reports, "
                "and sweep outputs. CI uses offline mode."
            ),
        ),
    ]
    for path in sorted((root / "docs").glob("**/*.md")) if (root / "docs").exists() else []:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if text.strip():
            docs.append(
                DocumentChunk(
                    id=str(path.relative_to(root)).replace("\\", "/"),
                    title=path.stem.replace("_", " ").title(),
                    text=text[:6000],
                    source=str(path.relative_to(root)).replace("\\", "/"),
                )
            )
    return docs


class LocalRetriever:
    def __init__(self, corpus: list[DocumentChunk] | None = None) -> None:
        self.corpus = corpus or default_corpus()
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform([chunk.text for chunk in self.corpus])

    def search(self, query: str, k: int = 4) -> list[dict]:
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).ravel()
        order = scores.argsort()[::-1][:k]
        return [
            {
                "id": self.corpus[index].id,
                "title": self.corpus[index].title,
                "source": self.corpus[index].source,
                "score": float(scores[index]),
                "snippet": self.corpus[index].text[:600],
            }
            for index in order
        ]

    def answer(self, question: str) -> dict:
        if is_unsafe_request(question):
            return {
                "answer": REFUSAL,
                "citations": [{"title": "Ethics Policy", "source": "docs/ethics.md"}],
                "safe": False,
            }
        hits = self.search(question)
        context = " ".join(hit["snippet"] for hit in hits[:3])
        causal_caution = ""
        if any(term in question.lower() for term in ["prove", "causal", "causes", "cause"]):
            causal_caution = (
                " The policy layer uses cautious causal language: fixed effects and lags improve "
                "the research design, but they do not prove causality by themselves."
            )
        answer = (
            "Based on the project documentation and aggregate dataset assets: "
            f"{context[:900]} "
            f"{causal_caution} "
            "For stronger claims, use the dashboard filters and cite the generated quality/model reports."
        )
        return {
            "answer": answer,
            "citations": [{"title": hit["title"], "source": hit["source"]} for hit in hits],
            "safe": True,
        }
