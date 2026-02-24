# Run AI Resume ATS Scanner Backend
Set-Location $PSScriptRoot\backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
