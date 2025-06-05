# main.py
"""Entry point of the application."""
from core.monitor import Monitor
from ui.app import App


def main() -> None:
    monitor = Monitor()      # domain / business-logic object
    app = App(monitor)       # GUI object (inherits from tk.Tk)
    app.mainloop()           # start event loop


if __name__ == "__main__":
    main()
