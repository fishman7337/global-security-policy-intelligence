from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def wandb_run(project: str, config: dict, job_type: str):
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
    try:
        import wandb

        artifact = wandb.Artifact(name=artifact_name, type=artifact_type)
        artifact.add_file(str(path))
        run.log_artifact(artifact)
    except Exception:
        return
