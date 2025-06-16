"""core/dummy_network_monitor.py – versión 3
Simulador de NetworkMonitor con intervalo de 15 s y métricas coherentes.

Cambios respecto a v2:
* `polling_interval` por defecto baja a 15 segundos.
* El % de uso de ancho de banda ahora es un número aleatorio realista
  entre 0 % y 90 % (evita valores casi cero).
* Se conservan IPv6, `error_history`, umbrales y alertas.
"""
from __future__ import annotations

import random
import threading
import time
from datetime import datetime
from typing import Callable, Optional, Dict, List, Tuple, Any

__all__ = ["DummyNetworkMonitor"]


class DummyNetworkMonitor:
    """Genera snapshots sintéticos imitando al monitor real."""

    def __init__(
        self,
        *,
        on_update: Optional[Callable[[dict], None]] = None,
        polling_interval: int = 15,
        interfaces_count: int = 4,
        bandwidth_threshold: int = 70,
        error_threshold: int = 5,
    ) -> None:
        self.on_update = on_update
        self.polling_interval = polling_interval
        self.bandwidth_threshold = bandwidth_threshold
        self.error_threshold = error_threshold

        self._stop_evt = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Estructuras de datos
        self.interfaces: Dict[str, Dict[str, Any]] = {}
        self.bandwidth_history: Dict[str, List[Tuple[str, float]]] = {}
        self.error_history: Dict[str, List[Tuple[str, int]]] = {}
        self.alerts: List[Dict[str, Any]] = []
        self._total_errors: Dict[str, int] = {}

        self._create_inventory(interfaces_count)

    # ------------------------------------------------------------------
    #  API pública
    # ------------------------------------------------------------------
    def start_monitoring(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="DummyNetMon")
        self._thread.start()

    def stop_monitoring(self):
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=2)

    # ------------------------------------------------------------------
    #  Internos
    # ------------------------------------------------------------------
    def _create_inventory(self, n: int):
        for i in range(n):
            name = f"GigabitEthernet0/{i}"
            speed = random.choice([100, 1000])  # Mb/s
            self.interfaces[name] = {
                "name": name,
                "description": f"Dummy interface {i}",
                "status": random.choice(["up", "down"]),
                "enabled": True,
                "ip": f"192.0.2.{i+1}",
                "ipv6": f"2001:db8::{i+1}",
                "speed": speed,
            }
            self.bandwidth_history[name] = []
            self.error_history[name] = []
            self._total_errors[name] = 0

    def _loop(self):
        while not self._stop_evt.is_set():
            self._simulate_cycle()
            time.sleep(self.polling_interval)

    def _simulate_cycle(self):
        ts = datetime.utcnow().isoformat(timespec="seconds")
        for name, meta in self.interfaces.items():
            # --- Bandwidth entre 0 y 90 % ---------------------------------
            bw_pct = random.uniform(0, 90)
            self.bandwidth_history[name].append((ts, bw_pct))
            self.bandwidth_history[name][:] = self.bandwidth_history[name][-288:]

            # --- Errores acumulados ---------------------------------------
            inc_errors = random.randint(0, 10)
            self._total_errors[name] += inc_errors
            self.error_history[name].append((ts, self._total_errors[name]))
            self.error_history[name][:] = self.error_history[name][-288:]

            # --- Alertas --------------------------------------------------
            if meta["status"] == "down":
                self._push_alert(ts, "critical", f"{name} is DOWN", name)
            elif inc_errors >= self.error_threshold:
                self._push_alert(ts, "warning", f"High error rate ({inc_errors}) on {name}", name)
            elif bw_pct >= self.bandwidth_threshold:
                self._push_alert(ts, "warning", f"High bandwidth ({bw_pct:.1f}%) on {name}", name)

        # --- Emit snapshot -----------------------------------------------
        snap = {
            "timestamp": ts,
            "interfaces": self.interfaces,
            "bandwidth_history": self.bandwidth_history,
            "error_history": self.error_history,
            "alerts": self.alerts,
        }
        if self.on_update:
            try:
                self.on_update(snap)
            except Exception:
                pass  # no detener hilo por error de la GUI

    def _push_alert(self, ts: str, sev: str, msg: str, iface: str):
        self.alerts.append({"timestamp": ts, "severity": sev, "message": msg, "interface": iface})
        self.alerts[:] = self.alerts[-100:]
