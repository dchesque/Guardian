@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo Guardian - Instalacao
echo ========================================
echo.

echo 1. Verificando Python...
python --version >nul 2>&1
if errorlevel 1 goto error_python

if exist venv goto skip_venv
echo 2. Criando ambiente virtual (venv)...
python -m venv venv
if errorlevel 1 goto error_venv

:skip_venv
echo 3. Atualizando pip...
venv\Scripts\python.exe -m pip install --upgrade pip

echo 4. Instalando dependencias (isso pode demorar)...
if not exist requirements.txt goto error_reqs
venv\Scripts\pip install -r requirements.txt
if errorlevel 1 goto error_pip

echo.
echo ========================================
echo Instalacao concluida com sucesso!
echo ========================================
echo.
echo Proximos passos:
echo 1. Edite config/settings.yaml com suas credenciais
echo 2. Configure o Google Drive (veja README.md)
echo 3. Execute start.bat para iniciar
echo.
pause
exit /b 0

:error_python
echo.
echo ERRO: Python nao encontrado no seu PATH!
echo Por favor, instale o Python e marque a opcao "Add to PATH".
pause
exit /b 1

:error_venv
echo.
echo ERRO: Falha ao criar o ambiente virtual (venv).
pause
exit /b 1

:error_reqs
echo.
echo ERRO: Arquivo requirements.txt nao encontrado.
pause
exit /b 1

:error_pip
echo.
echo ERRO: Falha ao instalar as dependencias. 
echo Verifique sua conexao com a internet ou se o Python 3.13 possui suporte para todas as libs.
pause
exit /b 1
