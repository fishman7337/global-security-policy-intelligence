"""Fault-tolerant Weights & Biases experiment-tracking helpers."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def wandb_run(project: str, config: dict, job_type: str):
    """Yield a W&B run or a no-network fallback run.

    Args:
        project: W&B project name.
        config: Experiment configuration to record.
        job_type: W&B job category.

    Yields:
        A W&B-compatible run object.

    """
    os.environ.setdefault("WANDB_MODE", os.getenv("WANDB_MODE", "offline"))
    try:
        import wandb

        with wandb.init(project=project, config=config, job_type=job_type) as run:
            yield run
    except Exception:

        class OfflineRun:
            name = "offline-fallback"

            def log(self, payload: dict) -> None:
                self.last_payload = payload

            def log_artifact(self, artifact) -> None:
                self.last_artifact = artifact

        yield OfflineRun()


def log_file_artifact(run, path: Path, artifact_name: str, artifact_type: str) -> None:
    """Log a file artifact when W&B is available.

    Args:
        run: Active W&B-compatible run object.
        path: Local artifact path.
        artifact_name: Stable artifact identifier.
        artifact_type: Artifact category.

    """
    try:
        import wandb

        artifact = wandb.Artifact(name=artifact_name, type=artifact_type)
        artifact.add_file(str(path))
        run.log_artifact(artifact)
    except Exception:
        return
