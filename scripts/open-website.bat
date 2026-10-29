@echo off
cd /d %~dp0..\frontend
echo Starting NeuroScan AI at http://localhost:4173
start http://localhost:4173/
npm run preview -- --host 0.0.0.0 --port 4173
