"""
Monitor de eventos de energia do Windows.
Detecta sleep, wake, lock, unlock.
"""

import threading
import ctypes
from ctypes import wintypes
from typing import Callable, Optional

from src.config_manager import get_config
from src.utils.logger import setup_logger


# Constantes Windows
WM_POWERBROADCAST = 0x0218
PBT_APMSUSPEND = 0x0004
PBT_APMRESUMESUSPEND = 0x0007
PBT_APMRESUMEAUTOMATIC = 0x0012

WM_WTSSESSION_CHANGE = 0x02B1
WTS_SESSION_LOCK = 0x7
WTS_SESSION_UNLOCK = 0x8


class PowerMonitor:
    """Monitora eventos de energia e sessão do Windows."""
    
    def __init__(self):
        config = get_config()
        self.logger = setup_logger("power_monitor", config.get("system.log_level", "INFO"))
        
        self.pause_on_lock = config.get("privacy.pause_on_lock", True)
        
        self._callbacks = {}
        self._is_running = False
        self._hwnd = None
    
    def register_callback(self, event: str, callback: Callable):
        """
        Registra callback para evento.
        
        Eventos:
        - 'on_sleep': Quando PC entra em sleep
        - 'on_wake': Quando PC acorda
        - 'on_lock': Quando tela é bloqueada
        - 'on_unlock': Quando tela é desbloqueada
        """
        self._callbacks[event] = callback
    
    def _window_proc(self, hwnd, msg, wparam, lparam):
        """Processa mensagens do Windows."""
        try:
            if msg == WM_POWERBROADCAST:
                if wparam == PBT_APMSUSPEND:
                    self.logger.info("Sistema entrando em sleep")
                    self._trigger('on_sleep')
                elif wparam in (PBT_APMRESUMESUSPEND, PBT_APMRESUMEAUTOMATIC):
                    self.logger.info("Sistema acordando")
                    self._trigger('on_wake')
            
            elif msg == WM_WTSSESSION_CHANGE:
                if wparam == WTS_SESSION_LOCK:
                    self.logger.info("Tela bloqueada")
                    if self.pause_on_lock:
                        self._trigger('on_lock')
                elif wparam == WTS_SESSION_UNLOCK:
                    self.logger.info("Tela desbloqueada")
                    if self.pause_on_lock:
                        self._trigger('on_unlock')
        except Exception as e:
            self.logger.error(f"Erro no power monitor: {e}")
        
        return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)
    
    def _trigger(self, event: str):
        """Dispara callback de evento."""
        if event in self._callbacks:
            try:
                self._callbacks[event]()
            except Exception as e:
                self.logger.error(f"Erro no callback {event}: {e}")
    
    def _message_loop(self):
        """Loop de mensagens do Windows."""
        try:
            # Criar janela invisível para receber mensagens
            WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM)
            
            wc = ctypes.windll.user32.WNDCLASSW()
            wc.lpfnWndProc = WNDPROC(self._window_proc)
            wc.lpszClassName = "PowerMonitorClass"
            
            ctypes.windll.user32.RegisterClassW(ctypes.byref(wc))
            
            self._hwnd = ctypes.windll.user32.CreateWindowExW(
                0, wc.lpszClassName, "PowerMonitor",
                0, 0, 0, 0, 0, None, None, None, None
            )
            
            # Registrar para notificações de sessão
            ctypes.windll.wtsapi32.WTSRegisterSessionNotification(self._hwnd, 0)
            
            self.logger.info("Power monitor iniciado")
            
            # Loop de mensagens
            msg = wintypes.MSG()
            while self._is_running:
                if ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0):
                    ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                    ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
                    
        except Exception as e:
            self.logger.error(f"Erro no message loop: {e}")
    
    def start(self):
        """Inicia monitoramento."""
        if self._is_running:
            return
        
        self._is_running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Para monitoramento."""
        self._is_running = False
        
        if self._hwnd:
            try:
                ctypes.windll.wtsapi32.WTSUnRegisterSessionNotification(self._hwnd)
                ctypes.windll.user32.DestroyWindow(self._hwnd)
            except:
                pass
