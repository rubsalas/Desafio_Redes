"""
Arranca el monitor y lanza la interfaz Tkinter.
"""
from __future__ import annotations

from core.dummy_network_monitor import DummyNetworkMonitor  # Cambia a NetworkMonitor en producción
from ui.app import App


def main() -> None:
    monitor = DummyNetworkMonitor()  # mismas firmas que el monitor real
    app = App(monitor)
    app.mainloop()


if __name__ == "__main__":
    main()
