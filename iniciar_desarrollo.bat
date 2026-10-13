@echo off
start "API FastAPI" cmd /k ".\venv\Scripts\uvicorn.exe api:app --reload"
start /D "frontend" "Frontend React" cmd /k "npm.cmd run dev"
