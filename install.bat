@echo off
setlocal enabledelayedexpansion

:: Garante que o script rode no diretorio onde ele esta localizado
cd /d "%~dp0"

echo ========================================
echo Guardian - Instalacao
echo ========================================
echo.

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo.
    echo DICA: Voce pode tentar executar o arquivo "setup_system.bat" 
    echo para instalar o Python e o FFmpeg automaticamente.
    echo.
    pause
    exit /b 1
)

:: Cria ambiente virtual se nao existir
if not exist venv (
    echo Criando ambiente virtual (venv)...
    python -m venv venv
    if errorlevel 1 (
        echo ERRO: Falha ao criar ambiente virtual!
        pause
        exit /b 1
    )
)

echo.
echo Atualizando pip...
venv\Scripts\python.exe -m pip install --upgrade pip

echo.
echo Instalando dependencias...
venv\Scripts\pip install -r requirements.txt

if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Instalacao concluida!
echo ========================================
echo.
echo Proximos passos:
echo 1. Edite config/settings.yaml com suas credenciais
echo 2. Configure o Google Drive (veja README.md)
echo 3. Execute start.bat para iniciar
echo.
pause
