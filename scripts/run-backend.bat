@echo off
set PYTHONPATH=%~dp0..
cd /d %~dp0backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
