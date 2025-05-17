@echo off
echo Starting Image Analysis App in development mode...

:: Start backend (async)
start cmd /k "cd backend && python -m app.main"

:: Wait for backend to initialize
echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

:: Start frontend
echo Starting frontend...
cd frontend && npm run dev

echo Development environment is stopping...
