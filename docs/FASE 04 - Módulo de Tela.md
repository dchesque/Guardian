# FASE 04 - Módulo de Tela

## Objetivo
Implementar captura de screenshots e análise usando IA com visão.

## Duração Estimada
3 horas

## Pré-requisitos
- Fases 01, 02 e 03 completas

---

## Entregas

### 1. src/screen/capture.py

```python
"""
Captura de screenshots da tela.
"""

import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List

import mss
from PIL import Image

from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import ensure_dir, get_today_folder


class ScreenCapture:
    """Captura screenshots em intervalos configuráveis."""
    
    def __init__(
        self,
        interval_seconds: int = 30,
        output_dir: str = "data/temp_screenshots",
        on_capture_ready: Optional[Callable[[Path], None]] = None
    ):
        config = get_config()
        self.logger = setup_logger("screen_capture", config.get("system.log_level", "INFO"))
        
        self.interval = interval_seconds
        self.output_dir = Path(output_dir)
        self.on_capture_ready = on_capture_ready
        
        self.monitor_index = config.get("screen.monitor", 0)
        self.format = config.get("screen.format", "jpg")
        self.quality = config.get("screen.quality", 70)
        
        # Privacidade
        self.excluded_apps = config.get("privacy.excluded_apps", [])
        self.excluded_windows = config.get("privacy.excluded_windows", [])
        
        self.is_running = False
        self.is_paused = False
        
        ensure_dir(self.output_dir)
        self.logger.info(f"ScreenCapture: intervalo={interval_seconds}s, monitor={self.monitor_index}")
    
    def _get_active_window_title(self) -> str:
        """Obtém título da janela ativa (Windows)."""
        try:
            import win32gui
            window = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(window)
        except:
            return ""
    
    def _should_skip_capture(self) -> bool:
        """Verifica se deve pular captura (app/janela excluída)."""
        title = self._get_active_window_title().lower()
        
        for app in self.excluded_apps:
            if app.lower() in title:
                self.logger.debug(f"Pulando captura: app excluído ({app})")
                return True
        
        for window in self.excluded_windows:
            if window.lower() in title:
                self.logger.debug(f"Pulando captura: janela excluída ({window})")
                return True
        
        return False
    
    def _capture_loop(self):
        """Loop principal de captura."""
        self.logger.info("Loop de captura iniciado")
        
        with mss.mss() as sct:
            monitors = sct.monitors
            
            # Selecionar monitor (0 = todos, 1+ = específico)
            if self.monitor_index < len(monitors):
                monitor = monitors[self.monitor_index]
            else:
                monitor = monitors[1]  # Monitor principal
            
            while self.is_running:
                try:
                    if self.is_paused or self._should_skip_capture():
                        time.sleep(self.interval)
                        continue
                    
                    # Capturar
                    screenshot = sct.grab(monitor)
                    
                    # Converter para PIL Image
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    
                    # Salvar
                    filepath = self._save_screenshot(img)
                    
                    if filepath and self.on_capture_ready:
                        self.on_capture_ready(filepath)
                    
                    time.sleep(self.interval)
                    
                except Exception as e:
                    self.logger.error(f"Erro na captura: {e}")
                    time.sleep(self.interval)
        
        self.logger.info("Loop de captura encerrado")
    
    def _save_screenshot(self, img: Image.Image) -> Optional[Path]:
        """Salva screenshot em arquivo."""
        try:
            today_dir = ensure_dir(self.output_dir / get_today_folder())
            timestamp = datetime.now().strftime("%Hh%Mm%Ss")
            
            if self.format == "jpg":
                filepath = today_dir / f"{timestamp}.jpg"
                img.save(filepath, "JPEG", quality=self.quality)
            else:
                filepath = today_dir / f"{timestamp}.png"
                img.save(filepath, "PNG")
            
            self.logger.debug(f"Screenshot salvo: {filepath.name}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar screenshot: {e}")
            return None
    
    def start(self) -> bool:
        """Inicia captura de tela."""
        if self.is_running:
            return False
        
        self.is_running = True
        self.is_paused = False
        
        self._capture_thread = threading.Thread(target=self._capture_loop)
        self._capture_thread.start()
        
        self.logger.info("Captura de tela iniciada")
        return True
    
    def stop(self):
        """Para captura de tela."""
        if not self.is_running:
            return
        
        self.is_running = False
        if hasattr(self, '_capture_thread'):
            self._capture_thread.join(timeout=10)
        
        self.logger.info("Captura de tela parada")
    
    def pause(self):
        """Pausa captura."""
        self.is_paused = True
        self.logger.info("Captura pausada")
    
    def resume(self):
        """Retoma captura."""
        self.is_paused = False
        self.logger.info("Captura retomada")
    
    def capture_once(self) -> Optional[Path]:
        """Captura uma única screenshot."""
        with mss.mss() as sct:
            monitors = sct.monitors
            monitor = monitors[min(self.monitor_index, len(monitors) - 1)]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            return self._save_screenshot(img)
    
    def get_monitors(self) -> List[dict]:
        """Lista monitores disponíveis."""
        with mss.mss() as sct:
            return [{'id': i, 'size': f"{m['width']}x{m['height']}"} for i, m in enumerate(sct.monitors)]
```

---

### 2. src/screen/analyzer.py

```python
"""
Analisador de screenshots usando IA com visão.
"""

from pathlib import Path
from typing import Optional
import threading
import queue

from src.api import get_openrouter_client, OpenRouterError
from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import ensure_dir, get_today_folder


class ScreenAnalyzer:
    """Analisa screenshots usando modelo de visão."""
    
    DEFAULT_PROMPT = """Analise esta screenshot e descreva brevemente:
1. Qual aplicativo/site está aberto
2. O que o usuário está fazendo
3. Qualquer texto importante visível

Seja conciso (máximo 3 linhas)."""
    
    def __init__(
        self,
        output_dir: str = "data/screen_analysis",
        model: Optional[str] = None,
        analysis_prompt: Optional[str] = None
    ):
        config = get_config()
        self.logger = setup_logger("screen_analyzer", config.get("system.log_level", "INFO"))
        
        self.output_dir = Path(output_dir)
        self.model = model or config.get("models.screen_analysis")
        self.prompt = analysis_prompt or self.DEFAULT_PROMPT
        
        self._queue = queue.Queue()
        self._is_running = False
        
        ensure_dir(self.output_dir)
        self.logger.info(f"ScreenAnalyzer: modelo={self.model}")
    
    def _worker(self):
        """Worker que processa fila de análise."""
        client = get_openrouter_client()
        
        while self._is_running or not self._queue.empty():
            try:
                screenshot_path = self._queue.get(timeout=1.0)
                self.logger.info(f"Analisando: {screenshot_path.name}")
                
                analysis = client.analyze_image(
                    screenshot_path,
                    prompt=self.prompt,
                    model=self.model
                )
                
                self._save_analysis(screenshot_path, analysis)
                
                # Deletar screenshot após análise (economizar espaço)
                self._delete_screenshot(screenshot_path)
                
                self._queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erro na análise: {e}")
    
    def _save_analysis(self, screenshot_path: Path, analysis: str):
        """Salva análise em arquivo do dia."""
        try:
            output_path = ensure_dir(self.output_dir / get_today_folder())
            analysis_file = output_path / "analise_tela.txt"
            
            timestamp = screenshot_path.stem  # Ex: "14h30m45s"
            
            with open(analysis_file, "a", encoding="utf-8") as f:
                f.write(f"\n[{timestamp}]\n{analysis}\n")
            
            self.logger.debug("Análise salva")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar análise: {e}")
    
    def _delete_screenshot(self, screenshot_path: Path):
        """Deleta screenshot após análise (se não for fazer backup)."""
        config = get_config()
        if not config.get("google_drive.backup.screenshots", False):
            try:
                screenshot_path.unlink()
                self.logger.debug(f"Screenshot deletado: {screenshot_path.name}")
            except:
                pass
    
    def start(self):
        """Inicia worker de análise."""
        if self._is_running:
            return
        
        self._is_running = True
        self._worker_thread = threading.Thread(target=self._worker)
        self._worker_thread.start()
        self.logger.info("Analisador iniciado")
    
    def stop(self):
        """Para worker de análise."""
        self._is_running = False
        if hasattr(self, '_worker_thread'):
            self._worker_thread.join(timeout=60)
        self.logger.info("Analisador parado")
    
    def add_to_queue(self, screenshot_path: Path):
        """Adiciona screenshot à fila de análise."""
        self._queue.put(screenshot_path)
        self.logger.debug(f"Screenshot na fila: {screenshot_path.name}")
    
    def analyze_file(self, screenshot_path: Path) -> str:
        """Analisa screenshot diretamente (síncrono)."""
        client = get_openrouter_client()
        return client.analyze_image(screenshot_path, prompt=self.prompt, model=self.model)
    
    def get_queue_size(self) -> int:
        """Retorna tamanho da fila."""
        return self._queue.qsize()
    
    def get_today_analysis(self) -> str:
        """Obtém todas as análises do dia."""
        analysis_file = self.output_dir / get_today_folder() / "analise_tela.txt"
        return analysis_file.read_text(encoding="utf-8") if analysis_file.exists() else ""
```

---

### 3. src/screen/__init__.py

```python
from src.screen.capture import ScreenCapture
from src.screen.analyzer import ScreenAnalyzer

__all__ = ["ScreenCapture", "ScreenAnalyzer"]
```

---

### 4. Atualizar src/main.py

Adicionar módulo de tela ao main.py:

```python
# Adicionar imports
from src.screen import ScreenCapture, ScreenAnalyzer

# Na classe Assistant, adicionar atributos no __init__:
self.screen_capture = None
self.screen_analyzer = None

# Adicionar método _setup_screen:
def _setup_screen(self):
    """Configura módulo de tela."""
    self.logger.info("Configurando módulo de tela...")
    
    interval = self.config.get("screen.capture_interval_seconds", 30)
    
    self.screen_analyzer = ScreenAnalyzer()
    
    self.screen_capture = ScreenCapture(
        interval_seconds=interval,
        on_capture_ready=self._on_screenshot_ready
    )
    
    self.logger.info("Módulo de tela: CONFIGURADO")

def _on_screenshot_ready(self, screenshot_path: Path):
    """Callback quando screenshot está pronto."""
    self.logger.debug(f"Nova screenshot: {screenshot_path.name}")
    if self.screen_analyzer:
        self.screen_analyzer.add_to_queue(screenshot_path)

# No setup(), adicionar:
if self.config.screen_enabled:
    self._setup_screen()
else:
    self.logger.info("Módulo de tela: DESATIVADO")

# No start(), adicionar:
if self.config.screen_enabled and self.screen_capture:
    self.screen_analyzer.start()
    self.screen_capture.start()

# No stop(), adicionar:
if self.screen_capture:
    self.screen_capture.stop()
if self.screen_analyzer:
    self.screen_analyzer.stop()
```

---

## Critérios de Aceite

- [ ] ScreenCapture captura screenshots no intervalo configurado
- [ ] Screenshots salvos como JPG com qualidade configurável
- [ ] ScreenAnalyzer processa fila de screenshots
- [ ] Análises salvas em arquivo por dia
- [ ] Callback on_capture_ready funciona
- [ ] Apps/janelas excluídas não são capturadas
- [ ] Screenshots deletados após análise (se backup desativado)
- [ ] Pause/resume funciona
- [ ] Integração com main.py

---

## Testes

```bash
# Testar captura (1 min, intervalo de 10s)
python -c "
from src.screen import ScreenCapture
import time

capture = ScreenCapture(interval_seconds=10)
print('Monitores:', capture.get_monitors())
capture.start()
time.sleep(60)
capture.stop()
"

# Testar análise de uma imagem
python -c "
from src.screen import ScreenAnalyzer

analyzer = ScreenAnalyzer()
# Colocar uma imagem de teste em test.jpg
result = analyzer.analyze_file('test.jpg')
print(result)
"

# Verificar arquivos em:
# - data/temp_screenshots/<hoje>/
# - data/screen_analysis/<hoje>/
```

---

## Próxima Fase
Prossiga para **FASE-05-STORAGE-DELIVERY.md**.