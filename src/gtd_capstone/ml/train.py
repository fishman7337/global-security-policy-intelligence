from __future__ import annotations

import argparse
import json

import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from gtd_capstone.config import ensure_artifact_dirs, get_settings
from gtd_capstone.data.repository import DataRepository
from gtd_capstone.ml.wandb_utils import log_file_artifact, wandb_run


FEATURES = [
    "iyear",
    "imonth",
    "region_txt",
    "country_txt",
    "attacktype1_txt",
    "targtype1_txt",
    "weaptype1_txt",
    "suicide",
    "property",
    "ishostkid",
]


def train_severity_classifier(sample_rows: int | None = None) -> dict:
    settings = get_settings()
    ensure_artifact_dirs(settings)
    df = DataRepository(settings).load_incidents(sample_rows=sample_rows)
    df = df[df["severity"].notna()].copy()

    numeric_features = ["iyear", "imonth", "suicide", "property", "ishostkid"]
    categorical_features = [
        "region_txt",
        "country_txt",
        "attacktype1_txt",
        "targtype1_txt",
        "weaptype1_txt",
    ]
    x = df[FEATURES]
    y = df["severity"]
    stratify = y if y.value_counts().min() >= 2 and y.nunique() > 1 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=42, stratify=stratify
    )
    model = Pipeline(
        steps=[
            (
                "preprocess",
                ColumnTransformer(
                    transformers=[
                        ("num", StandardScaler(), numeric_features),
                        (
                            "cat",
                            OneHotEncoder(handle_unknown="ignore", min_frequency=3),
                            categorical_features,
                        ),
                    ]
                ),
            ),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=120,
                    max_depth=12,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                    class_weight="balanced_subsample",
                ),
            ),
        ]
    )
    config = {
        "model": "RandomForestClassifier",
        "target": "severity",
        "features": FEATURES,
        "rows": int(len(df)),
        "tracker": "wandb",
    }
    with wandb_run(settings.wandb_project, config=config, job_type="train") as run:
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        metrics = {
            "accuracy": float(accuracy_score(y_test, pred)),
            "macro_f1": float(f1_score(y_test, pred, average="macro")),
            "weighted_f1": float(f1_score(y_test, pred, average="weighted")),
            "train_rows": int(len(x_train)),
            "test_rows": int(len(x_test)),
        }
        run.log(metrics)
        report = classification_report(y_test, pred, output_dict=True, zero_division=0)
        model_dir = settings.artifact_dir / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / "severity_classifier.joblib"
        metrics_path = model_dir / "severity_metrics.json"
        joblib.dump(model, model_path)
        metrics_path.write_text(json.dumps({"metrics": metrics, "report": report}, indent=2), "utf-8")
        log_file_artifact(run, model_path, "severity-classifier", "model")
        log_file_artifact(run, metrics_path, "severity-classifier-metrics", "metrics")
    return {"metrics": metrics, "model_path": str(model_path), "metrics_path": str(metrics_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train GTD severity classifier with W&B tracking.")
    parser.add_argument("--sample-rows", type=int, default=None)
    args = parser.parse_args()
    print(json.dumps(train_severity_classifier(sample_rows=args.sample_rows), indent=2))


if __name__ == "__main__":
    main()
