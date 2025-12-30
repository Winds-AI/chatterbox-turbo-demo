@echo off
echo Starting Chatterbox Turbo - Streamlit + FastAPI
echo.

echo [1/2] Starting FastAPI backend...
start "Chatterbox Backend" cmd /k "cd backend && python main.py"
timeout /t 3 /nobreak >nul

echo [2/2] Starting Streamlit frontend...
echo Frontend will open in your browser...
streamlit run frontend/app.py

pause
