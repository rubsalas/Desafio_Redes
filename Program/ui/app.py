# ui/app.py
"""
Tkinter GUI wrapped in a class App(tk.Tk).

The UI depends on core.monitor.Monitor, but the Monitor
has **no** dependency on Tkinter – clean separation.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core.monitor import Monitor


class App(tk.Tk):
    def __init__(self, monitor: Monitor) -> None:
        super().__init__()
        self.title("Monitor demo")
        self.geometry("640x480")
        self.resizable(False, False)

        self._monitor = monitor
        self._build_gui()

    # --------------------------------------------------
    def _build_gui(self) -> None:
        """Create all widgets and place them with pack()."""
        # ---------- top bar ----------
        top = ttk.Frame(self, padding=10)
        top.pack(side="top", fill="x")

        ttk.Button(
            top, text="Refresh data", command=self._refresh
        ).pack(side="left")

        self._lbl_counter = ttk.Label(top, text="Calls: 0")
        self._lbl_counter.pack(side="left", padx=10)

        # ---------- Matplotlib figure ----------
        self._fig = Figure(figsize=(5, 3), dpi=100)
        self._ax = self._fig.add_subplot(111)

        self._canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._refresh()  # draw first plot

    # --------------------------------------------------
    def _refresh(self) -> None:
        """Ask Monitor for new data and redraw the bar chart."""
        data = self._monitor.get_data()
        self._lbl_counter.config(text=f"Calls: {self._monitor.call_count()}")

        self._ax.clear()
        self._ax.bar(list("ABCDE"), data, color="#4a90e2", edgecolor="black")
        self._ax.set_ylim(0, 10)
        self._ax.set_title("Live random data")
        self._ax.set_ylabel("Value")

        self._canvas.draw_idle()
