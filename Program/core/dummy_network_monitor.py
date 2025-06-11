"""
core/dummy_network_monitor.py
=============================================

Un sustituto de NetworkMonitor para pruebas de la interfaz.
Genera datos sintéticos y los envía al callback `on_update` cada
`polling_interval` segundos, imitando la estructura de snapshot del
monitor real.
"""
from __future__ import annotations

import random
import threading
import time
from datetime import datetime
from typing import Callable, Optional, Dict, List, Tuple

__all__ = ["DummyNetworkMonitor"]


class DummyNetworkMonitor:
    """Monitor compatible con la API pública de NetworkMonitor."""

    def __init__(
        self,
        *,
        on_update: Optional[Callable[[dict], None]] = None,
        polling_interval: int = 5,
        interfaces_count: int = 4,
    ) -> None:
        self.on_update = on_update
        self.polling_interval = polling_interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # --- datos simulados ---
        self.interfaces: Dict[str, Dict] = {}
        self.bandwidth_history: Dict[str, List[Tuple[str, float]]] = {}
        self.alerts: List[Dict] = []
        self._last_octets: Dict[str, int] = {}

        self._build_fake_inventory(interfaces_count)

    # ------------------------------------------------------------------
    # API pública consumida por la GUI
    # ------------------------------------------------------------------
    def start_monitoring(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="DummyNetworkMonitor"
        )
        self._thread.start()

    def stop_monitoring(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    # ------------------------------------------------------------------
    # Lógica privada
    # ------------------------------------------------------------------
    def _build_fake_inventory(self, n: int) -> None:
        for i in range(n):
            name = f"GigabitEthernet0/{i}"
            self.interfaces[name] = {
                "name": name,
                "description": f"Dummy interface {i}",
                "status": random.choice(["up", "down"]),
                "enabled": True,
                "ip": f"192.0.2.{i+1}",
                "speed": 1000,
            }
            self.bandwidth_history[name] = []
            self._last_octets[name] = 0

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            self._simulate_cycle()
            time.sleep(self.polling_interval)

    def _simulate_cycle(self) -> None:
        ts = datetime.utcnow().isoformat(timespec="seconds")

        for name in self.interfaces:
            # Incremento de octetos ficticios
            self._last_octets[name] += random.randint(10_000, 120_000)
            bw_pct = random.uniform(0, 90)

            history = self.bandwidth_history[name]
            history.append((ts, bw_pct))
            history[:] = history[-288:]  # máx. 24 h si intervalo = 5 min

            if random.random() < 0.05:  # probabilidad de alerta
                self.alerts.append(
                    {
                        "timestamp": ts,
                        "severity": random.choice(["info", "warning", "critical"]),
                        "message": f"Random alert on {name}",
                        "interface": name,
                    }
                )
                self.alerts[:] = self.alerts[-50:]

        if self.on_update:
            snapshot = {
                "timestamp": ts,
                "interfaces": self.interfaces,
                "bandwidth_history": self.bandwidth_history,
                "alerts": self.alerts,
            }
            try:
                self.on_update(snapshot)
            except Exception:
                # No interrumpir el hilo por errores de la UI.
                pass
