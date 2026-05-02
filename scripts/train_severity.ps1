$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src;$env:PYTHONPATH"
if (-not $env:WANDB_MODE) {
    $env:WANDB_MODE = "offline"
}
python -m gtd_capstone.ml.train --sample-rows 30000
