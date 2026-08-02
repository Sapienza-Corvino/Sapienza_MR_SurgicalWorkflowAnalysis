@echo off
title Google Drive OAuth Token Generator

echo =======================================================
echo     Google Drive OAuth Token Generator Setup
echo =======================================================
echo.

:: 1. Verifico se Python e disponibile
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRORE] Python non e installato o non e presente nel PATH del sistema.
    echo Per favore installa Python prima di continuare.
    echo.
    pause
    exit /b 1
)

:: 2. Creazione e attivazione ambiente virtuale locale in config\.venv_oauth
set "VENV_DIR=%~dp0.venv_oauth"
if not exist "%VENV_DIR%" (
    echo [*] Creazione ambiente virtuale Python in config\.venv_oauth...
    python -m venv "%VENV_DIR%"
)

echo [*] Attivazione ambiente virtuale...
call "%VENV_DIR%\Scripts\activate.bat"

echo [*] Verifica e installazione dipendenze Google OAuth...
pip install --quiet google-auth-oauthlib google-api-python-client google-auth

echo.
echo [*] Avvio dello script di autenticazione OAuth nel browser...
echo.

python "%~dp0..\src\tools\get_oauth_token.py"

echo.
pause
