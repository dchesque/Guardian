@echo off
setlocal
echo ========================================
echo Guardian - Setup Sistema
echo ========================================
echo.

echo Verificando winget...
winget --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: winget nao encontrado!
    echo Este script requer Windows 10/11 com winget instalado.
    echo Por favor, instale as dependencias manualmente ou atualize o Windows.
    pause
    exit /b 1
)

echo.
echo Instalando Python 3.11...
winget install -e --id Python.Python.3.11 --scope machine --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo AVISO: Falha ao instalar Python via winget ou ja instalado.
)

echo.
echo Instalando FFmpeg...
winget install -e --id Gyan.FFmpeg --scope machine --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo AVISO: Falha ao instalar FFmpeg via winget ou ja instalado.
)

echo.
echo ========================================
echo Processo concluido!
echo ========================================
echo.
echo IMPORTANTE:
echo 1. VOCE PRECISA REINICIAR SEU TERMINAL (ou o PC) para que o Windows
echo    reconheca o Python e o FFmpeg no seu PATH.
echo.
echo 2. Depois de reiniciar, execute o install.bat para finalizar.
echo.
pause
