"""
Arranca el monitor y lanza la interfaz Tkinter.
"""
from __future__ import annotations
from ui.app import NetworkMonitorApp

def main() -> None:
    app = NetworkMonitorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
