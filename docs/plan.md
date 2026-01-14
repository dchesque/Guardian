# PRD - Voice & Screen Assistant

## Documento de Requisitos do Produto
**Versão:** 1.0  
**Data:** Dezembro 2024  
**Autor:** Equipe de Desenvolvimento

---

## 1. Visão Geral

### 1.1 Resumo Executivo

O **Voice & Screen Assistant** é um aplicativo desktop para Windows que captura áudio ambiente e screenshots da tela do usuário ao longo do dia, transcreve e analisa esse conteúdo usando IA, e gera um resumo estratégico diário entregue por email e salvo no Google Drive.

### 1.2 Problema

Profissionais ocupados perdem informações valiosas ao longo do dia:
- Ideias mencionadas em conversas que são esquecidas
- Decisões tomadas que não são documentadas
- Compromissos verbais que se perdem
- Contexto de trabalho que não é registrado

### 1.3 Solução

Um assistente invisível que:
- Roda 100% em background, sem popups ou interações
- Captura e transcreve tudo que é falado
- Captura e analisa tudo que aparece na tela
- Gera um resumo inteligente no final do dia
- Entrega o resumo por email e faz backup no Google Drive

---

## 2. Objetivos

### 2.1 Objetivos Primários

| Objetivo | Métrica de Sucesso |
|----------|-------------------|
| Captura contínua de áudio | 100% do tempo ativo gravado |
| Captura contínua de tela | Screenshots a cada 30s |
| Transcrição precisa | Taxa de erro < 15% |
| Resumo diário útil | Entrega às 22h todos os dias |
| Zero fricção | Nenhuma interação necessária |

### 2.2 Objetivos Secundários

- Backup seguro de todos os dados
- Custo mensal previsível (~R$150)
- Privacidade configurável (exclusão de apps/janelas)
- Fácil manutenção e atualização

---

## 3. Público-Alvo

### 3.1 Usuário Principal

**Empreendedor/Profissional ocupado** que:
- Tem múltiplas responsabilidades
- Participa de muitas conversas/reuniões
- Trabalha em vários projetos simultaneamente
- Quer documentar decisões sem esforço manual

### 3.2 Persona

**Usuário** - Empresário/Profissional focado em produtividade
- Usa Windows
- Não tem GPU dedicada no notebook
- Quer manter os custos sob controle
- Precisa de resumos estratégicos sobre negócios e atividades diárias

---

## 4. Requisitos Funcionais

### 4.1 Módulo de Áudio

| ID | Requisito | Prioridade |
|----|-----------|------------|
| AUD-01 | Gravar áudio do microfone em chunks de duração configurável | Alta |
| AUD-02 | Transcrever áudio usando API configurável (default: Groq Whisper) | Alta |
| AUD-03 | Salvar transcrições localmente e no Google Drive | Alta |
| AUD-04 | Upload de arquivos de áudio para Google Drive | Alta |
| AUD-05 | Deletar áudio local após upload bem-sucedido | Média |
| AUD-06 | Permitir ativar/desativar módulo | Alta |
| AUD-07 | Configurar dispositivo de entrada de áudio | Baixa |
| AUD-08 | Configurar qualidade/formato do áudio | Média |

### 4.2 Módulo de Tela

| ID | Requisito | Prioridade |
|----|-----------|------------|
| SCR-01 | Capturar screenshots em intervalo configurável | Alta |
| SCR-02 | Analisar screenshots usando API configurável (default: Gemini) | Alta |
| SCR-03 | Salvar análises localmente e no Google Drive | Alta |
| SCR-04 | Permitir ativar/desativar módulo | Alta |
| SCR-05 | Configurar monitor a ser capturado | Baixa |
| SCR-06 | Configurar qualidade/formato da imagem | Média |
| SCR-07 | Excluir apps/janelas específicas da captura | Média |

### 4.3 Módulo de Resumo

| ID | Requisito | Prioridade |
|----|-----------|------------|
| SUM-01 | Gerar resumo diário usando API configurável (default: GPT-4o-mini) | Alta |
| SUM-02 | Usar prompt personalizado do usuário | Alta |
| SUM-03 | Combinar transcrições e análises de tela no resumo | Alta |
| SUM-04 | Salvar resumo no Google Drive | Alta |
| SUM-05 | Executar em horário configurável | Alta |

### 4.4 Módulo de Entrega

| ID | Requisito | Prioridade |
|----|-----------|------------|
| DEL-01 | Enviar resumo por email (SMTP) | Alta |
| DEL-02 | Configurar email de destino | Alta |
| DEL-03 | Enviar alertas de erro por email | Média |
| DEL-04 | Permitir ativar/desativar email | Alta |

### 4.5 Módulo de Armazenamento

| ID | Requisito | Prioridade |
|----|-----------|------------|
| STO-01 | Integrar com Google Drive API | Alta |
| STO-02 | Criar estrutura de pastas por data | Alta |
| STO-03 | Upload de áudios, transcrições, análises e resumos | Alta |
| STO-04 | Limpeza automática de arquivos antigos | Média |
| STO-05 | Configurar retenção por tipo de arquivo | Média |
| STO-06 | Backup seletivo (escolher o que enviar) | Média |

### 4.6 Módulo de Sistema

| ID | Requisito | Prioridade |
|----|-----------|------------|
| SYS-01 | Rodar em background sem janela/popup | Alta |
| SYS-02 | Iniciar automaticamente com Windows | Alta |
| SYS-03 | Detectar sleep/wake e retomar operação | Alta |
| SYS-04 | Pausar quando tela estiver bloqueada | Média |
| SYS-05 | Logs de execução | Alta |
| SYS-06 | Limpeza automática de logs antigos | Baixa |

### 4.7 Configuração

| ID | Requisito | Prioridade |
|----|-----------|------------|
| CFG-01 | Arquivo YAML para todas as configurações | Alta |
| CFG-02 | API key OpenRouter configurável | Alta |
| CFG-03 | Modelos LLM configuráveis por função | Alta |
| CFG-04 | Validação de configurações na inicialização | Alta |
| CFG-05 | Prompt personalizado em arquivo separado | Alta |

---

## 5. Requisitos Não-Funcionais

### 5.1 Performance

| Requisito | Especificação |
|-----------|---------------|
| Uso de RAM | < 100 MB |
| Uso de CPU (idle) | < 5% |
| Uso de CPU (gravando) | < 15% |
| Tempo de startup | < 10 segundos |

### 5.2 Confiabilidade

| Requisito | Especificação |
|-----------|---------------|
| Disponibilidade | 99% do tempo que o PC estiver ligado |
| Recuperação de falhas | Auto-restart em caso de crash |
| Tolerância a erros de rede | Retry com backoff exponencial |

### 5.3 Segurança

| Requisito | Especificação |
|-----------|---------------|
| Armazenamento de credenciais | Arquivos locais protegidos |
| Transmissão de dados | HTTPS para todas as APIs |
| Dados sensíveis | Nunca logados em texto claro |

### 5.4 Usabilidade

| Requisito | Especificação |
|-----------|---------------|
| Instalação | Script batch único |
| Configuração | Arquivo YAML documentado |
| Operação | Zero interação após setup |

---

## 6. Arquitetura

### 6.1 Stack Tecnológica

| Componente | Tecnologia |
|------------|------------|
| Linguagem | Python 3.11+ |
| Gateway de APIs | OpenRouter |
| Transcrição | Groq Whisper (via OpenRouter) |
| Análise de tela | Gemini Flash-Lite (via OpenRouter) |
| Resumo | GPT-4o-mini (via OpenRouter) |
| Captura de áudio | sounddevice + scipy |
| Captura de tela | mss |
| Google Drive | google-api-python-client |
| Email | smtplib (nativo) |
| Agendamento | schedule |
| Configuração | pyyaml |
| Windows | pywin32 |

### 6.2 Estrutura de Diretórios

```
voice-screen-assistant/
├── config/
│   ├── settings.yaml
│   ├── prompt.txt
│   └── credentials/
│       ├── google_drive.json
│       └── token.json
├── src/
│   ├── main.py
│   ├── config_manager.py
│   ├── api/
│   │   └── openrouter_client.py
│   ├── audio/
│   │   ├── recorder.py
│   │   └── transcriber.py
│   ├── screen/
│   │   ├── capture.py
│   │   └── analyzer.py
│   ├── summary/
│   │   └── generator.py
│   ├── storage/
│   │   ├── local_storage.py
│   │   └── drive_manager.py
│   ├── delivery/
│   │   └── email_sender.py
│   ├── system/
│   │   ├── scheduler.py
│   │   ├── power_monitor.py
│   │   └── startup.py
│   └── utils/
│       ├── logger.py
│       └── helpers.py
├── data/
│   ├── temp_audio/
│   ├── temp_screenshots/
│   ├── transcriptions/
│   └── screen_analysis/
├── logs/
├── requirements.txt
├── install.bat
├── start.bat
├── stop.bat
└── README.md
```

### 6.3 Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────┐
│                         ENTRADA                             │
├─────────────────────────────────────────────────────────────┤
│  Microfone ──► recorder.py ──► temp_audio/                  │
│  Tela ──────► capture.py ───► temp_screenshots/             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      PROCESSAMENTO                          │
├─────────────────────────────────────────────────────────────┤
│  temp_audio/ ──► transcriber.py ──► OpenRouter (Groq)       │
│                                          │                  │
│                                          ▼                  │
│                                   transcriptions/           │
│                                                             │
│  temp_screenshots/ ──► analyzer.py ──► OpenRouter (Gemini)  │
│                                              │              │
│                                              ▼              │
│                                       screen_analysis/      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        AGREGAÇÃO                            │
├─────────────────────────────────────────────────────────────┤
│  transcriptions/ ─┬─► generator.py ──► OpenRouter (GPT)     │
│  screen_analysis/ ┘           │                             │
│                               ▼                             │
│                          resumo.md                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         SAÍDA                               │
├─────────────────────────────────────────────────────────────┤
│  resumo.md ──► email_sender.py ──► Email (SMTP)             │
│           └──► drive_manager.py ──► Google Drive            │
│                                                             │
│  temp_audio/ ──► drive_manager.py ──► Google Drive          │
│  transcriptions/ ──► drive_manager.py ──► Google Drive      │
│  screen_analysis/ ──► drive_manager.py ──► Google Drive     │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Configuração

### 7.1 settings.yaml

```yaml
# ===== API =====
openrouter:
  api_key: "sk-or-v1-xxxxxxxxxxxx"

# ===== MODELOS LLM =====
models:
  transcription: "groq/whisper-large-v3"
  screen_analysis: "google/gemini-2.0-flash-lite-001"
  summary: "openai/gpt-4o-mini"

# ===== MÓDULO DE ÁUDIO =====
audio:
  enabled: true
  input_device: null
  chunk_duration_minutes: 10
  format: "mp3"
  quality: "low"

# ===== MÓDULO DE TELA =====
screen:
  enabled: true
  capture_interval_seconds: 30
  monitor: 0
  format: "jpg"
  quality: 70

# ===== AGENDAMENTO =====
schedule:
  summary_time: "22:00"
  timezone: "America/Sao_Paulo"

# ===== GOOGLE DRIVE =====
google_drive:
  enabled: true
  credentials_file: "config/credentials/google_drive.json"
  token_file: "config/credentials/token.json"
  folder_name: "Assistente IA"
  backup:
    audio: true
    screenshots: false
    transcriptions: true
    screen_analysis: true
    summaries: true
  cleanup:
    enabled: true
    audio_retention_days: 30
    screenshots_retention_days: 7

# ===== EMAIL =====
email:
  enabled: true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  use_tls: true
  sender_email: "seu_email@gmail.com"
  sender_password: "xxxx xxxx xxxx xxxx"
  recipient_email: "seu_email@gmail.com"
  send_daily_summary: true
  send_on_error: true

# ===== PROMPT =====
prompt:
  file: "config/prompt.txt"

# ===== SISTEMA =====
system:
  start_with_windows: true
  start_minimized: true
  log_level: "INFO"
  log_retention_days: 7

# ===== PRIVACIDADE =====
privacy:
  pause_on_lock: true
  excluded_apps: []
  excluded_windows: []
```

### 7.2 prompt.txt (Exemplo)

```
Analise as transcrições de áudio e análises de tela do meu dia e me entregue:

## 1. Resumo Executivo
- O que aconteceu hoje em 3-5 frases

## 2. Decisões Tomadas
- Liste todas as decisões que mencionei ou tomei

## 3. Compromissos e Prazos
- Qualquer coisa que prometi fazer ou data que mencionei

## 4. Ideias e Insights
- Ideias que tive durante o dia (negócios, projetos, melhorias)

## 5. Tarefas Pendentes
- O que preciso fazer amanhã ou nos próximos dias

## 6. Alertas
- Algo que parece urgente ou que não posso esquecer

Seja objetivo e direto. Use bullet points.
```

---

## 8. Estimativa de Custos

### 8.1 Custo Mensal (10h/dia de uso)

| Componente | Modelo | Custo/mês |
|------------|--------|-----------|
| Transcrição de áudio | Groq Whisper | ~R$36 |
| Análise de tela | Gemini Flash-Lite | ~R$105 |
| Resumo diário | GPT-4o-mini | ~R$5 |
| Taxa OpenRouter (~5%) | - | ~R$7 |
| **TOTAL** | | **~R$153** |

### 8.2 Cenários de Uso

| Configuração | Custo/mês |
|--------------|-----------|
| Só áudio | ~R$40 |
| Só tela | ~R$110 |
| Áudio + Tela | ~R$153 |

---

## 9. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Falha de API | Média | Alto | Retry com backoff, logs detalhados |
| Espaço em disco cheio | Baixa | Alto | Limpeza automática, alertas |
| Credenciais expostas | Baixa | Alto | Arquivos locais, nunca em logs |
| PC desligado inesperadamente | Média | Médio | Salvar estado frequentemente |
| Custo acima do esperado | Baixa | Médio | Monitoramento de uso, alertas |

---

## 10. Fases de Desenvolvimento

O desenvolvimento está dividido em 6 fases incrementais:

| Fase | Nome | Descrição | Duração Est. |
|------|------|-----------|--------------|
| 1 | Fundação | Estrutura, config, logging | 2h |
| 2 | API Client | Cliente OpenRouter unificado | 2h |
| 3 | Áudio | Gravação e transcrição | 3h |
| 4 | Tela | Captura e análise | 3h |
| 5 | Storage & Delivery | Drive, email, resumo | 3h |
| 6 | Sistema | Background, startup, polish | 2h |

**Total estimado: 15 horas de desenvolvimento**

Cada fase possui documentação detalhada em arquivo separado:
- `FASE-01-FUNDACAO.md`
- `FASE-02-API-CLIENT.md`
- `FASE-03-AUDIO.md`
- `FASE-04-TELA.md`
- `FASE-05-STORAGE-DELIVERY.md`
- `FASE-06-SISTEMA.md`

---

## 11. Critérios de Aceite

### 11.1 Funcionalidade

- [ ] App inicia automaticamente com Windows
- [ ] Grava áudio em chunks configuráveis
- [ ] Transcreve áudio via OpenRouter
- [ ] Captura screenshots em intervalos configuráveis
- [ ] Analisa screenshots via OpenRouter
- [ ] Gera resumo diário no horário configurado
- [ ] Envia resumo por email
- [ ] Faz backup no Google Drive
- [ ] Limpa arquivos antigos automaticamente

### 11.2 Qualidade

- [ ] Zero popups ou janelas durante operação normal
- [ ] Recupera de falhas automaticamente
- [ ] Logs úteis para debug
- [ ] Configuração validada na inicialização

### 11.3 Performance

- [ ] Uso de RAM < 100 MB
- [ ] Uso de CPU < 15% durante gravação
- [ ] Startup < 10 segundos

---

## 12. Glossário

| Termo | Definição |
|-------|-----------|
| Chunk | Segmento de áudio de duração fixa |
| OpenRouter | Gateway de APIs que unifica acesso a múltiplos LLMs |
| Groq | Provedor de API para Whisper (transcrição) |
| Gemini | Modelo do Google para análise de imagens |
| GPT-4o-mini | Modelo da OpenAI para geração de texto |
| SMTP | Protocolo para envio de emails |
| OAuth | Protocolo de autenticação usado pelo Google Drive |

---

## 13. Referências

- OpenRouter: https://openrouter.ai
- Groq: https://groq.com
- Google AI Studio: https://aistudio.google.com
- Google Drive API: https://developers.google.com/drive
- Python sounddevice: https://python-sounddevice.readthedocs.io
- Python mss: https://python-mss.readthedocs.io