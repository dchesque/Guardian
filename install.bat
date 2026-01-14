@echo off
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

echo.
echo Instalando dependencias...
pip install -r requirements.txt

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
