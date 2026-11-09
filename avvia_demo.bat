@echo off
chcp 65001 >nul
echo ========================================
echo   Diablo Build Advisor - Avvio Completo
echo ========================================
echo.

REM Verifica Python
where python >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato nel PATH.
    pause
    exit /b 1
)

REM Avvia Waitress su porta 5101
echo [1/2] Avvio server su http://127.0.0.1:5101 ...
start "" "C:/Users/skine/AppData/Local/hermes/cache/scratch/diablo_work_d085/.venv/Scripts/python.exe" -m waitress --listen=127.0.0.1:5101 app:app

REM Attendi che il server sia pronto
timeout /t 5 >nul

REM Avvia Cloudflare Tunnel
echo [2/2] Avvio tunnel Cloudflare ...
start "" "C:/Users/skine/AppData/Local/hermes/cache/scratch/d093_copia_fase2_test_20261107/cloudflared.exe" tunnel --url http://127.0.0.1:5101

echo.
echo ========================================
echo   Entrambi i processi sono avviati.
echo   Controlla la finestra di cloudflared
echo   per l'URL HTTPS pubblico (trycloudflare.com).
echo ========================================
pause