# Changelog - Guardian

## [1.0.2] - 2026-01-14

### Fixed
- Erro de sintaxe "... foi inesperado" no `install.bat` causado por caracteres especiais.
- Incompatibilidade de pacotes (`scipy`, `numpy`) com Python 3.13 através de requisitos flexíveis.

## [1.0.1] - 2026-01-14

## [1.0.0] - 2026-01-14

### Added
- Estrutura inicial do projeto Guardian.
- Módulo de captura de áudio com segmentos de 10 min.
- Transcrição via OpenRouter (Whisper v3).
- Captura de tela periódica (30s) com análise via Gemini 2.0.
- Sincronização com Google Drive.
- Geração de resumo diário automático.
- Envio de relatórios por e-mail.
- Scripts de automação para setup e instalação.
- Integração com inicialização do Windows.
