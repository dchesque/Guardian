# AGENT.md - Instruções para IA Desenvolvedora

## Sobre Este Documento

Este arquivo contém instruções para uma IA (Claude, GPT, etc.) desenvolver o projeto **Voice & Screen Assistant**. 

---

## 🎯 Objetivo

Implementar um app Python para Windows que:
- Grava áudio do microfone continuamente
- Captura screenshots periodicamente  
- Transcreve e analisa usando IA (OpenRouter)
- Gera resumo diário
- Envia por email e faz backup no Google Drive
- Roda 100% em background

---

## 📚 Documentos do Projeto

```
PRD.md                      # Requisitos (LEIA PRIMEIRO)
FASE-01-FUNDACAO.md         # Estrutura, config, logging
FASE-02-API-CLIENT.md       # Cliente OpenRouter
FASE-03-AUDIO.md            # Gravação e transcrição
FASE-04-TELA.md             # Captura e análise de tela
FASE-05-STORAGE-DELIVERY.md # Drive, email, resumo
FASE-06-SISTEMA.md          # Scheduler, power, startup
AGENT.md                    # Este arquivo
```

---

## 🔄 Fluxo de Trabalho

### Para Cada Fase:

1. **Leia** o arquivo da fase completamente
2. **Verifique** os pré-requisitos
3. **Implemente** cada arquivo na ordem listada
4. **Teste** conforme especificado
5. **Valide** os critérios de aceite
6. **Prossiga** para próxima fase

---

## 📋 Checklist Rápido

### Fase 1 - Fundação
- [ ] Estrutura de diretórios
- [ ] requirements.txt
- [ ] config/settings.yaml
- [ ] src/utils/logger.py
- [ ] src/utils/helpers.py
- [ ] src/config_manager.py
- [ ] src/main.py (esqueleto)
- [ ] Scripts batch

### Fase 2 - API Client
- [ ] src/api/openrouter_client.py
- [ ] src/api/models.py
- [ ] Testar conexão

### Fase 3 - Áudio
- [ ] src/audio/recorder.py
- [ ] src/audio/transcriber.py
- [ ] Testar gravação

### Fase 4 - Tela
- [ ] src/screen/capture.py
- [ ] src/screen/analyzer.py
- [ ] Testar captura

### Fase 5 - Storage & Delivery
- [ ] src/storage/drive_manager.py
- [ ] src/delivery/email_sender.py
- [ ] src/summary/generator.py

### Fase 6 - Sistema
- [ ] src/system/scheduler.py
- [ ] src/system/power_monitor.py
- [ ] src/system/startup.py
- [ ] src/main.py (final)

---

## ⚠️ Regras Importantes

### FAÇA:
- ✅ Leia cada fase antes de implementar
- ✅ Siga a estrutura exata de diretórios
- ✅ Use imports absolutos (from src.xxx)
- ✅ Adicione logs em operações importantes
- ✅ Crie `__init__.py` em cada pasta
- ✅ Teste antes de prosseguir

### NÃO FAÇA:
- ❌ Pular fases
- ❌ Modificar estrutura sem necessidade
- ❌ Ignorar critérios de aceite
- ❌ Hardcode de credenciais
- ❌ Imports relativos

---

## 🔧 Problemas Comuns

### ModuleNotFoundError
```python
# Verifique __init__.py em cada pasta
# Verifique sys.path no main.py
```

### API key inválida
```
# Verifique settings.yaml
# Key começa com "sk-or-v1-"
```

### Google Drive - Permissão negada
```
# Delete token.json e reautentique
```

### Microfone não encontrado
```python
import sounddevice as sd
print(sd.query_devices())  # Veja IDs disponíveis
```

---

## 📝 Template de Resposta

Ao completar uma fase:

```
## Fase X Completa ✅

### Arquivos Criados
- path/arquivo1.py
- path/arquivo2.py

### Testes
- [x] Teste 1: OK
- [x] Teste 2: OK

### Próximo
Pronto para Fase X+1
```

---

## 🚀 Comando de Início

```
Leia PRD.md e FASE-01-FUNDACAO.md.
Implemente a Fase 1 completamente,
criando todos os arquivos e testando.
```

---

## 📊 Projeto Completo Quando:

1. ✅ `python src/main.py` inicia sem erros
2. ✅ Áudio gravado e transcrito
3. ✅ Screenshots capturados e analisados
4. ✅ Resumo gerado no horário
5. ✅ Email enviado
6. ✅ Backup no Drive
7. ✅ Roda em background
8. ✅ Inicia com Windows
9. ✅ Pausa no sleep

---

## 💡 Dicas

### Imports
```python
# CORRETO
from src.config_manager import get_config
from src.utils.logger import setup_logger

# ERRADO
from .config_manager import get_config
```

### Logging
```python
config = get_config()
logger = setup_logger("modulo", config.get("system.log_level"))

logger.info("Iniciando...")
logger.error(f"Erro: {e}")
```

---

## 🎓 Referências

| API | Doc |
|-----|-----|
| OpenRouter | openrouter.ai/docs |
| Google Drive | developers.google.com/drive |
| sounddevice | python-sounddevice.readthedocs.io |
| mss | python-mss.readthedocs.io |

---

**Siga fase por fase. Boa sorte!**