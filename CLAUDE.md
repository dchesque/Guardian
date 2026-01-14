# CLAUDE.md - Diretrizes do Projeto Guardian

## Comandos de Build e Execução
- **Instalação**: `install.bat` (Cria venv e instala dependências)
- **Execução**: `start.bat` ou `python src/main.py`
- **Setup de Sistema**: `setup_system.bat` (Instala Python/FFmpeg via winget)

## Estilo de Código
- **Linguagem**: Python 3.11+
- **Imports**: Sempre use imports absolutos (ex: `from src.utils.logger import setup_logger`).
- **Nomenclatura**: CamelCase para Classes, snake_case para funções e variáveis.
- **Tipagem**: Use type hints sempre que possível.
- **Logging**: Utilize o logger centralizado em `src.utils.logger`.

## Princípios de Design
1. **Background First**: O sistema deve operar sem interrupção do usuário.
2. **Privacy First**: Dados sensíveis e capturas devem ser processados com cautela e respeitar o `.gitignore`.
3. **Resiliência**: Tratamento de erros em chamadas de API e operações de I/O.
