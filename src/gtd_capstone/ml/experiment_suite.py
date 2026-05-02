from __future__ import annotations

import argparse
import json

import joblib
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from gtd_capstone.config import ensure_artifact_dirs, get_settings
from gtd_capstone.data.repository import DataRepository
from gtd_capstone.features.store import materialize_feature_set
from gtd_capstone.ml.wandb_utils import log_file_artifact, wandb_run


NUMERIC = ["iyear", "imonth", "suicide", "property", "ishostkid"]
CATEGORICAL = ["region_txt", "country_txt", "attacktype1_txt", "targtype1_txt", "weaptype1_txt"]
FEATURES = [*NUMERIC, *CATEGORICAL]


def preprocess() -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("num", StandardScaler(), NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=5), CATEGORICAL),
        ]
    )


def classifier(family: str):
    if family == "logistic_regression":
        return LogisticRegression(max_iter=500, n_jobs=-1, class_weight="balanced")
    if family == "extra_trees":
        return ExtraTreesClassifier(n_estimators=200, random_state=42, n_jobs=-1, class_weight="balanced")
    return RandomForestClassifier(
        n_estimators=200,
        max_depth=14,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced_subsample",
    )


def run_classification(task: str, sample_rows: int | None, family: str) -> dict:
    settings = get_settings()
    ensure_artifact_dirs(settings)
    df = DataRepository(settings).load_incidents(sample_rows=sample_rows)
    feature_frame = materialize_feature_set(df)
    target = "severity" if task == "severity" else task
    x = feature_frame[FEATURES]
    y = feature_frame[target]
    stratify = y if y.value_counts().min() >= 2 and y.nunique() > 1 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=42, stratify=stratify
    )
    model = Pipeline([("preprocess", preprocess()), ("model", classifier(family))])
    config = {"task": task, "family": family, "rows": int(len(df)), "features": FEATURES}
    with wandb_run(settings.wandb_project, config=config, job_type=f"train-{task}") as run:
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        metrics = {
            "accuracy": float(accuracy_score(y_test, pred)),
            "macro_f1": float(f1_score(y_test, pred, average="macro", zero_division=0)),
            "weighted_f1": float(f1_score(y_test, pred, average="weighted", zero_division=0)),
        }
        run.log(metrics)
        model_path = settings.artifact_dir / "models" / f"{task}_{family}.joblib"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_path)
        log_file_artifact(run, model_path, f"{task}-{family}", "model")
    return {"task": task, "family": family, "metrics": metrics, "model_path": str(model_path)}


def run_regression(target: str, sample_rows: int | None) -> dict:
    settings = get_settings()
    df = DataRepository(settings).load_incidents(sample_rows=sample_rows)
    x = df[FEATURES]
    y = df[target]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42)
    model = Pipeline(
        [
            ("preprocess", preprocess()),
            ("model", RandomForestRegressor(n_estimators=160, max_depth=14, random_state=42, n_jobs=-1)),
        ]
    )
    with wandb_run(settings.wandb_project, {"task": target, "kind": "regression"}, "train-regression") as run:
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        metrics = {
            "mae": float(mean_absolute_error(y_test, pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
            "r2": float(r2_score(y_test, pred)),
        }
        run.log(metrics)
    return {"task": target, "metrics": metrics}


def run_clustering(sample_rows: int | None, clusters: int = 8) -> dict:
    settings = get_settings()
    df = DataRepository(settings).load_incidents(sample_rows=sample_rows)
    x = preprocess().fit_transform(df[FEATURES])
    model = MiniBatchKMeans(n_clusters=clusters, random_state=42, batch_size=2048, n_init="auto")
    labels = model.fit_predict(x)
    score = silhouette_score(x, labels) if len(set(labels)) > 1 and x.shape[0] <= 20000 else None
    with wandb_run(settings.wandb_project, {"task": "incident-clustering", "clusters": clusters}, "cluster") as run:
        run.log({"clusters": clusters, "silhouette": score or 0.0})
    return {"task": "incident-clustering", "clusters": clusters, "silhouette": score}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run extreme GTD experiment suite.")
    parser.add_argument("--task", choices=["severity", "success", "nkill", "nwound", "clustering"], default="severity")
    parser.add_argument("--model-family", default="random_forest")
    parser.add_argument("--sample-rows", type=int, default=10000)
    args = parser.parse_args()
    if args.task in {"severity", "success"}:
        result = run_classification(args.task, args.sample_rows, args.model_family)
    elif args.task in {"nkill", "nwound"}:
        result = run_regression(args.task, args.sample_rows)
    else:
        result = run_clustering(args.sample_rows)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
