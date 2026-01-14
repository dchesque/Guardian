# Guardian - Assistente de Produtividade e Compliance

> Monitoramento inteligente de atividades via Áudio, Tela e Teclado com análise avançada por IA.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![IA](https://img.shields.io/badge/AI-OpenRouter-FF5722?style=for-the-badge&logo=openai&logoColor=white)](https://openrouter.ai/)
[![Windows](https://img.shields.io/badge/Windows-Background-0078D6?style=for-the-badge&logo=windows&logoColor=white)](#)
[![Privacy](https://img.shields.io/badge/Privacy-First-4CAF50?style=for-the-badge&logo=shield&logoColor=white)](#-privacidade-e-segurança)

O **Guardian** é um assistente desktop para Windows projetado para operar 100% em segundo plano. Ele captura áudio ambiente, screenshots e registros de teclado, utilizando modelos de IA de última geração para analisar o contexto, detectar riscos de conformidade e gerar resumos de produtividade automáticos.

---

## � Funcionalidades Principais

### 🎙️ Inteligência Auditiva (Audio)
- **Captura Contínua**: Grava em segmentos configuráveis para fácil organização.
- **Transcrição de Alta Precisão**: Utiliza o modelo **Whisper Large v3** para converter voz em texto instantaneamente.
- **Análise Contextual**: Identifica assuntos tratados e decisões tomadas em conversas.

### 🖥️ Visão Computacional (Screen)
- **Monitoramento de Tela**: Captura screenshots periódicas sem interromper o fluxo de trabalho.
- **Análise Visual Avançada**: Utiliza **Google Gemini 2.0** para descrever atividades, identificar sites/aplicativos e detectar comportamentos fora do padrão.

### ⌨️ Registro de Atividades (Keyboard)
- **Keylogging Estratégico**: Monitora a digitação para entender a intencionalidade do usuário e identificar riscos de segurança ou vazamento de dados.
- **Auditoria de Comportamento**: Analisa o tom e o conteúdo das comunicações locais.

### 📊 Resumo e Sincronização
- **Resumo Executivo Diário**: Compilação de todas as métricas do dia em um relatório estratégico via **GPT-4o-mini**.
- **Backup em Nuvem**: Sincronização automática com o **Google Drive**.
- **Notificações por E-mail**: Entrega do resumo diário e alertas críticos diretamente na sua caixa de entrada.

---

## 🛠️ Arquitetura do Sistema

O sistema é modular e extensível, utilizando as melhores tecnologias de processamento local e APIs de nuvem:

| Módulo | Tecnologia Principal | Função |
| :--- | :--- | :--- |
| **Áudio** | `sounddevice` + `Whisper` | Gravação e Transcrição |
| **Visão** | `mss` + `Gemini` | Captura e Análise de Tela |
| **Lógica** | `OpenRouter` | Gateway de Múltiplos LLMs |
| **Storage** | `Google Drive API` | Backup e Persistência |
| **Sistema** | `pywin32` + `schtasks` | Background e Startup |

---

## � Guia de Instalação

### Pré-requisitos
- **Windows 10/11**
- **Conexão com Internet** (para APIs e Sincronização)

### Passo a Passo

1. **Baixe o projeto** para o seu PC.

2. **Configuração Automática do Ambiente**:
   Se você não possui Python ou FFmpeg instalados, execute o script de setup:
   ```powershell
   setup_system.bat
   ```
   > [!IMPORTANT]
   > Reinicie o seu terminal após a conclusão deste passo.

3. **Instalação das Dependências**:
   Prepare o ambiente virtual e instale os pacotes necessários:
   ```powershell
   install.bat
   ```

4. **Credenciais do Google Cloud**:
   - Baixe seu arquivo `credentials.json` do [Google Console](https://console.cloud.google.com/).
   - Renomeie para `google_drive.json`.
   - Coloque em `config/credentials/`.

---

## ⚙️ Configuração Principal

Toda a personalização é feita via `config/settings.yaml`.

### 🔑 APIs e Chaves
Insira sua chave da [OpenRouter](https://openrouter.ai/) para habilitar as IAs.
```yaml
openrouter:
  api_key: "SUA_CHAVE_AQUI"
```

### ☁️ Google Drive
```yaml
google_drive:
  enabled: true
  folder_name: "Assistente Guardian" # Nome da pasta no Drive
```

### 📧 E-mail (Relatórios)
Utilize uma [Senha de App](https://myaccount.google.com/apppasswords) para usar o Gmail.
```yaml
email:
  sender_email: "seu@email.com"
  sender_password: "sua_senha_de_app"
```

---

## 🛡️ Privacidade e Segurança

- **Processamento em Background**: O app não possui interface gráfica visível para evitar interrupções.
- **Zonas de Exclusão**: É possível configurar aplicativos e janelas que não devem ser capturados.
- **Segurança de Dados**: Chaves de API e tokens de acesso são armazenados localmente e ignorados pelo controle de versão.
- **Transparência**: O sistema registra todos os eventos importantes na pasta `/logs`.

---

## � Licença

Este projeto é de uso pessoal/corporativo privado. Consulte os termos de uso antes de redistribuir.

---
*Guardian - Inteligência e Segurança na sua Produtividade.*
