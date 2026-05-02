$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src;$env:PYTHONPATH"
uvicorn gtd_capstone.api.main:app --reload --host 127.0.0.1 --port 8000
