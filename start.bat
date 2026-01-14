@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo Guardian - Iniciando
echo ========================================

if not exist venv (
    echo.
    echo ERRO: Ambiente virtual nao encontrado! 
    echo Por favor, execute o install.bat primeiro.
    echo.
    pause
    exit /b 1
)

:: Usamos python.exe em vez de pythonw.exe para ver erros se ocorrerem
:: O comando 'start' abre em uma nova janela.
venv\Scripts\python.exe src\main.py

if errorlevel 1 (
    echo.
    echo ERRO: O assistente parou inesperadamente.
    echo Verifique as mensagens acima para diagnostico.
    echo.
    pause
)
