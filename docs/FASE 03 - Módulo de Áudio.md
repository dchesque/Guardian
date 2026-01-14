# FASE 03 - Módulo de Áudio

## Objetivo
Implementar gravação contínua de áudio do microfone e transcrição automática.

## Duração Estimada
3 horas

## Pré-requisitos
- Fase 01 e 02 completas
- Microfone funcionando no Windows
- FFmpeg instalado (para conversão de áudio)

---

## Entregas

### 1. src/audio/recorder.py

```python
"""
Gravador de áudio do microfone.
Grava em chunks de duração configurável e salva como MP3.
"""

import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import ensure_dir, get_today_folder


class AudioRecorder:
    """Gravador de áudio do microfone."""
    
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = np.int16
    
    def __init__(
        self,
        chunk_duration_minutes: int = 10,
        output_dir: str = "data/temp_audio",
        on_chunk_ready: Optional[Callable[[Path], None]] = None
    ):
        config = get_config()
        self.logger = setup_logger("audio_recorder", config.get("system.log_level", "INFO"))
        
        self.chunk_duration = chunk_duration_minutes * 60
        self.output_dir = Path(output_dir)
        self.on_chunk_ready = on_chunk_ready
        
        self.input_device = config.get("audio.input_device")
        self.audio_format = config.get("audio.format", "mp3")
        self.quality = config.get("audio.quality", "low")
        
        self.is_recording = False
        self.is_paused = False
        self._audio_queue = queue.Queue()
        self._current_chunk = []
        self._chunk_start_time = None
        
        ensure_dir(self.output_dir)
        self.logger.info(f"AudioRecorder: {chunk_duration_minutes}min chunks")
    
    def _get_bitrate(self) -> str:
        return {"low": "16k", "medium": "32k", "high": "64k"}.get(self.quality, "16k")
    
    def _audio_callback(self, indata, frames, time, status):
        if status:
            self.logger.warning(f"Audio status: {status}")
        if not self.is_paused:
            self._audio_queue.put(indata.copy())
    
    def _process_audio(self):
        while self.is_recording or not self._audio_queue.empty():
            try:
                audio_data = self._audio_queue.get(timeout=1.0)
                self._current_chunk.append(audio_data)
                
                duration = len(self._current_chunk) * len(audio_data) / self.SAMPLE_RATE
                if duration >= self.chunk_duration:
                    self._save_current_chunk()
            except queue.Empty:
                continue
        
        if self._current_chunk:
            self._save_current_chunk()
    
    def _save_current_chunk(self):
        if not self._current_chunk:
            return
        
        try:
            audio_data = np.concatenate(self._current_chunk)
            chunk_dir = ensure_dir(self.output_dir / get_today_folder())
            
            start = self._chunk_start_time or datetime.now()
            end = datetime.now()
            filename = f"{start.strftime('%Hh%M')}-{end.strftime('%Hh%M')}"
            
            wav_path = chunk_dir / f"{filename}.wav"
            wavfile.write(wav_path, self.SAMPLE_RATE, audio_data)
            
            if self.audio_format == "mp3":
                mp3_path = chunk_dir / f"{filename}.mp3"
                self._convert_to_mp3(wav_path, mp3_path)
                wav_path.unlink()
                final_path = mp3_path
            else:
                final_path = wav_path
            
            self.logger.info(f"Chunk salvo: {final_path.name}")
            
            if self.on_chunk_ready:
                self.on_chunk_ready(final_path)
            
            self._current_chunk = []
            self._chunk_start_time = datetime.now()
        except Exception as e:
            self.logger.error(f"Erro ao salvar chunk: {e}")
    
    def _convert_to_mp3(self, wav_path: Path, mp3_path: Path):
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_wav(str(wav_path))
            audio.export(str(mp3_path), format="mp3", bitrate=self._get_bitrate())
        except ImportError:
            import subprocess
            subprocess.run(["ffmpeg", "-y", "-i", str(wav_path), "-b:a", self._get_bitrate(), str(mp3_path)], capture_output=True)
    
    def start(self) -> bool:
        if self.is_recording:
            return False
        
        try:
            self.is_recording = True
            self.is_paused = False
            self._chunk_start_time = datetime.now()
            
            self._process_thread = threading.Thread(target=self._process_audio)
            self._process_thread.start()
            
            self._stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype=self.DTYPE,
                device=self.input_device,
                callback=self._audio_callback
            )
            self._stream.start()
            
            self.logger.info("Gravação iniciada")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao iniciar: {e}")
            self.is_recording = False
            return False
    
    def stop(self):
        if not self.is_recording:
            return
        
        self.is_recording = False
        if hasattr(self, '_stream'):
            self._stream.stop()
            self._stream.close()
        if hasattr(self, '_process_thread'):
            self._process_thread.join(timeout=10)
        self.logger.info("Gravação parada")
    
    def pause(self):
        self.is_paused = True
        self.logger.info("Gravação pausada")
    
    def resume(self):
        self.is_paused = False
        self.logger.info("Gravação retomada")
    
    def get_input_devices(self) -> list:
        devices = sd.query_devices()
        return [{'id': i, 'name': d['name']} for i, d in enumerate(devices) if d['max_input_channels'] > 0]
```

---

### 2. src/audio/transcriber.py

```python
"""
Transcritor de áudio usando OpenRouter API.
"""

from pathlib import Path
from typing import Optional
import threading
import queue

from src.api import get_openrouter_client, OpenRouterError
from src.config_manager import get_config
from src.utils.logger import setup_logger
from src.utils.helpers import ensure_dir, get_today_folder


class AudioTranscriber:
    """Transcritor de áudio com fila de processamento."""
    
    def __init__(self, output_dir: str = "data/transcriptions", model: Optional[str] = None):
        config = get_config()
        self.logger = setup_logger("transcriber", config.get("system.log_level", "INFO"))
        
        self.output_dir = Path(output_dir)
        self.model = model or config.get("models.transcription")
        
        self._queue = queue.Queue()
        self._is_running = False
        
        ensure_dir(self.output_dir)
        self.logger.info(f"Transcritor: modelo={self.model}")
    
    def _worker(self):
        client = get_openrouter_client()
        
        while self._is_running or not self._queue.empty():
            try:
                audio_path = self._queue.get(timeout=1.0)
                self.logger.info(f"Transcrevendo: {audio_path.name}")
                
                transcription = client.transcribe_audio(audio_path, model=self.model, language="pt")
                self._save_transcription(audio_path, transcription)
                
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erro: {e}")
    
    def _save_transcription(self, audio_path: Path, transcription: str):
        try:
            output_path = ensure_dir(self.output_dir / get_today_folder())
            transcript_file = output_path / "transcricao.txt"
            
            with open(transcript_file, "a", encoding="utf-8") as f:
                f.write(f"\n[{audio_path.stem}]\n{transcription}\n")
            
            self.logger.info(f"Transcrição salva")
        except Exception as e:
            self.logger.error(f"Erro ao salvar: {e}")
    
    def start(self):
        if self._is_running:
            return
        self._is_running = True
        self._worker_thread = threading.Thread(target=self._worker)
        self._worker_thread.start()
    
    def stop(self):
        self._is_running = False
        if hasattr(self, '_worker_thread'):
            self._worker_thread.join(timeout=30)
    
    def add_to_queue(self, audio_path: Path):
        self._queue.put(audio_path)
    
    def transcribe_file(self, audio_path: Path) -> str:
        return get_openrouter_client().transcribe_audio(audio_path, model=self.model)
    
    def get_today_transcription(self) -> str:
        transcript_file = self.output_dir / get_today_folder() / "transcricao.txt"
        return transcript_file.read_text(encoding="utf-8") if transcript_file.exists() else ""
```

---

### 3. src/audio/__init__.py

```python
from src.audio.recorder import AudioRecorder
from src.audio.transcriber import AudioTranscriber

__all__ = ["AudioRecorder", "AudioTranscriber"]
```

---

## Critérios de Aceite

- [ ] AudioRecorder grava áudio do microfone
- [ ] Chunks salvos no intervalo configurado (MP3)
- [ ] AudioTranscriber processa fila de arquivos
- [ ] Transcrições salvas em arquivo por dia
- [ ] Callback on_chunk_ready funciona
- [ ] Pause/resume funciona
- [ ] Integração com main.py

---

## Testes

```bash
# Testar gravação (2 min, chunks de 1 min)
python -c "
from src.audio import AudioRecorder
import time

recorder = AudioRecorder(chunk_duration_minutes=1)
recorder.start()
time.sleep(120)
recorder.stop()
"

# Verificar arquivos em data/temp_audio/<hoje>/
```

---

## Próxima Fase
Prossiga para **FASE-04-TELA.md**.