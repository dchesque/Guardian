@echo off
cd /d "%~dp0"
echo Iniciando Guardian...
if exist venv (
    start venv\Scripts\pythonw.exe src\main.py
) else (
    echo ERRO: Ambiente virtual nao encontrado! 
    echo Por favor, execute o install.bat primeiro.
    pause
)
