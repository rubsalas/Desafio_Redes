"""ui/app.py – *Desafío Redes*
================================
Versión con IPv6 y gráfico de errores.

Paginas (máx. 4):
* Tabla horizontal con Status, IPv4, IPv6, Speed, Description.
* Notebook interno con dos tabs:
  - *Bandwidth %* (línea)
  - *Errors* (línea acumulada)

Mantiene barra superior y lista de alertas.
"""
from __future__ import annotations

import queue
import tkinter as tk
from datetime import datetime
from typing import Any, Dict, List, Tuple

import matplotlib
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import ttk

matplotlib.use("TkAgg")

__all__ = ["App"]

###############################################################################
#  Frames reutilizables                                                       #
###############################################################################

class TopBar(ttk.Frame):
    def __init__(self, master: tk.Misc, start_cb, stop_cb):  # type: ignore[name-defined]
        super().__init__(master, padding=8)
        self._start_cb, self._stop_cb = start_cb, stop_cb
        self.columnconfigure(2, weight=1)

        ttk.Label(self, text="Desafío Redes", font=("Helvetica", 18, "bold")).grid(row=0, column=0, sticky="w")
        self._led = ttk.Label(self, text="●", font=("Helvetica", 14), foreground="red")
        self._led.grid(row=0, column=1, padx=6)
        self._lbl_time = ttk.Label(self, text="—")
        self._lbl_time.grid(row=0, column=2, sticky="e", padx=6)
        self._btn_start = ttk.Button(self, text="Start", command=self._start_cb)
        self._btn_start.grid(row=0, column=3, padx=(6, 3))
        self._btn_stop = ttk.Button(self, text="Stop", command=self._stop_cb, state="disabled")
        self._btn_stop.grid(row=0, column=4, padx=(3, 6))

    def set_running(self, running: bool):
        self._led.configure(foreground="green" if running else "red")
        self._btn_start.configure(state="disabled" if running else "normal")
        self._btn_stop.configure(state="normal" if running else "disabled")

    def set_timestamp(self, ts: str):
        self._lbl_time.configure(text=ts)


class _LinePlot(ttk.Frame):
    """Base para plots con Matplotlib."""
    def __init__(self, master: tk.Misc, y_label: str):
        super().__init__(master)
        self._iface: str | None = None
        self._fig = Figure(figsize=(5, 3), dpi=100)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_ylabel(y_label)
        self._line = None
        canvas = FigureCanvasTkAgg(self._fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvas = canvas

    def _reset(self, title: str, y_label: str | None = None, ylim: Tuple[int,int] | None = None):
        self._ax.clear()
        self._ax.set_title(title)
        if y_label:
            self._ax.set_ylabel(y_label)
        if ylim:
            self._ax.set_ylim(*ylim)
        self._line = None
        self._canvas.draw_idle()

    def _update_line(self, series: List[Tuple[str, float]], ylim: Tuple[int,int] | None = None):
        if not series:
            return
        x = np.arange(len(series))
        y = [v for _, v in series]
        labels = [ts.split("T")[1] for ts, _ in series]
        if self._line is None:
            (self._line,) = self._ax.plot(x, y, "-o")
        else:
            self._line.set_data(x, y)
        step = max(1, len(x) // 8)
        self._ax.set_xticks(x[::step])
        self._ax.set_xticklabels(labels[::step], rotation=45, ha="right", fontsize=7)
        self._ax.set_xlim(0, len(x) - 1)
        if ylim:
            self._ax.set_ylim(*ylim)
        self._canvas.draw_idle()


class BandwidthPlot(_LinePlot):
    def __init__(self, master: tk.Misc, bw_threshold: int):
        super().__init__(master, "% BW usage")
        self._threshold = bw_threshold

    def set_interface(self, iface: str):
        self._iface = iface
        self._reset(f"Bandwidth — {iface}", "% BW usage", (0, 100))
        self._ax.axhline(self._threshold, linestyle="--", color="red")

    def update_history(self, hist: Dict[str, List[Tuple[str, float]]]):
        if self._iface and self._iface in hist:
            series = hist[self._iface][-60:]
            self._update_line(series, (0, 100))


class ErrorPlot(_LinePlot):
    def __init__(self, master: tk.Misc, error_threshold: int):
        super().__init__(master, "Total errors")
        self._threshold = error_threshold

    def set_interface(self, iface: str):
        self._iface = iface
        self._reset(f"Errors — {iface}")
        self._ax.axhline(self._threshold, linestyle="--", color="red")

    def update_history(self, hist: Dict[str, List[Tuple[str, int]]]):
        if self._iface and self._iface in hist:
            series = hist[self._iface][-60:]        # lista: [(ts, total_errors)]
            if len(series) < 2:
                return                              # aún no hay delta
            # ── NUEVO: calcular Δerrores por intervalo ───────────────────
            deltas = [
                (series[i][0], series[i][1] - series[i-1][1])
                for i in range(1, len(series))
            ]
            self._update_line(deltas, ylim=None)    # ahora graficamos delt


class InterfacePage(ttk.Frame):
    FIELDS = ("Status", "IPv4", "IPv6", "Speed (Mb/s)", "Description")

    def __init__(self, master: tk.Misc, bw_thr: int, err_thr: int):
        super().__init__(master, padding=10)
        self._bw_thr, self._err_thr = bw_thr, err_thr
        self._iface: str | None = None

        # Table horizontal
        table = ttk.Frame(self)
        table.grid(row=0, column=0, sticky="ew")
        for col, field in enumerate(self.FIELDS):
            ttk.Label(table, text=field, font=("Helvetica", 10, "bold")).grid(row=0, column=col, padx=6, pady=(0,2))
        self._vals: Dict[str, ttk.Label] = {}
        for col, field in enumerate(self.FIELDS):
            lbl = ttk.Label(table, text="—", width=20, anchor="center")
            lbl.grid(row=1, column=col, padx=6, pady=(0,4))
            self._vals[field] = lbl

        # inner notebook with plots
        self._plots_nb = ttk.Notebook(self)
        self._plots_nb.grid(row=1, column=0, sticky="nsew", pady=(10,0))
        self._bw_plot = BandwidthPlot(self._plots_nb, self._bw_thr)
        self._plots_nb.add(self._bw_plot, text="Bandwidth %")
        self._err_plot = ErrorPlot(self._plots_nb, self._err_thr)
        self._plots_nb.add(self._err_plot, text="Errors")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    def set_interface(self, name: str, data: Dict[str, Any]):
        self._iface = name
        self._bw_plot.set_interface(name)
        self._err_plot.set_interface(name)
        self._vals["Status"].configure(text=data.get("status", "—"))
        self._vals["IPv4"].configure(text=data.get("ip", "—"))
        self._vals["IPv6"].configure(text=data.get("ipv6", "—"))
        self._vals["Speed (Mb/s)"].configure(text=data.get("speed", "—"))
        self._vals["Description"].configure(text=data.get("description", ""))

    def refresh(self,
                bw_hist: Dict[str, List[Tuple[str, float]]],
                err_hist: Dict[str, List[Tuple[str, int]]]):
        self._bw_plot.update_history(bw_hist)
        self._err_plot.update_history(err_hist)


class AlertsFrame(ttk.Frame):
    COLS = ("Time", "Severity", "Iface", "Message")
    def __init__(self, master: tk.Misc):
        super().__init__(master, padding=10)
        self._tree = ttk.Treeview(self, columns=self.COLS, show="headings", height=6)
        self._tree.pack(fill="both", expand=True)
        for c in self.COLS:
            self._tree.heading(c, text=c)
            self._tree.column(c, anchor="center")
    def update(self, alerts: List[Dict[str,Any]]):
        self._tree.delete(*self._tree.get_children())
        for a in alerts[-100:]:
            self._tree.insert("", "end", values=(a["timestamp"].split("T")[1], a["severity"], a.get("interface",""), a["message"]))

###############################################################################
#  Main App                                                                   #
###############################################################################

class App(tk.Tk):
    """Ventana principal que orquesta Monitor ↔ GUI."""

    POLL_MS = 1_000  # chequeo de cola cada segundo
    MAX_PAGES = 4

    def __init__(self, monitor: Any):
        super().__init__()
        self.title("Desafío Redes")
        self.geometry("960x720")
        self.minsize(800, 600)

        # --- Dependencias -------------------------------------------------
        self._monitor = monitor
        self._queue: queue.Queue[dict] = queue.Queue()
        if hasattr(monitor, "on_update"):
            monitor.on_update = self._queue.put  # type: ignore[arg-type]

        # Umbrales leídos del monitor o valores de reserva
        self._bw_thr = getattr(monitor, "bandwidth_threshold", 70)
        self._err_thr = getattr(monitor, "error_threshold", 5)

        self._running = False
        self._page_ifaces: List[str | None] = [None] * self.MAX_PAGES

        # --- Construcción de UI -----------------------------------------
        self._build_ui()
        self.after(self.POLL_MS, self._pump_queue)

    # ------------------------------------------------------------------
    def _build_ui(self):
        # Barra superior
        self._top = TopBar(self, start_cb=self._start_monitor, stop_cb=self._stop_monitor)
        self._top.pack(fill="x")

        # Notebook principal con páginas por interfaz
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True)
        self._pages: List[InterfacePage] = []
        for idx in range(self.MAX_PAGES):
            page = InterfacePage(self._nb, self._bw_thr, self._err_thr)
            self._nb.add(page, text=f"Iface {idx+1}")
            self._pages.append(page)

        # Lista de alertas inferior
        self._alerts = AlertsFrame(self)
        self._alerts.pack(fill="both")

    # ------------------------------------------------------------------
    # Control del monitor (botones Start/Stop)
    def _start_monitor(self):
        if self._running:
            return
        if hasattr(self._monitor, "start_monitoring"):
            self._monitor.start_monitoring()
        self._running = True
        self._top.set_running(True)

    def _stop_monitor(self):
        if not self._running:
            return
        if hasattr(self._monitor, "stop_monitoring"):
            self._monitor.stop_monitoring()
        self._running = False
        self._top.set_running(False)

    # ------------------------------------------------------------------
    # Cola de snapshots
    def _pump_queue(self):
        try:
            while True:
                snap = self._queue.get_nowait()
                self._handle_snapshot(snap)
        except queue.Empty:
            pass
        self.after(self.POLL_MS, self._pump_queue)

    def _handle_snapshot(self, snap: dict):
        # Timestamp en TopBar
        ts = snap.get("timestamp") or datetime.utcnow().isoformat(timespec="seconds")
        self._top.set_timestamp(ts.split("T")[1])

        interfaces: Dict[str, Dict[str, Any]] = snap.get("interfaces", {})
        bw_hist: Dict[str, List[Tuple[str, float]]] = snap.get("bandwidth_history", {})
        err_hist: Dict[str, List[Tuple[str, int]]] = snap.get("error_history", {})

        # Asignar primeras N interfaces a páginas y refrescar datos
        first_ifaces = list(interfaces.keys())[: self.MAX_PAGES]
        for idx, iface in enumerate(first_ifaces):
            if self._page_ifaces[idx] != iface:
                self._page_ifaces[idx] = iface
                self._nb.tab(idx, text=iface)
            self._pages[idx].set_interface(iface, interfaces[iface])
            self._pages[idx].refresh(bw_hist, err_hist)

        # Alertas
        self._alerts.update(snap.get("alerts", []))

    # ------------------------------------------------------------------
    def destroy(self):  # noqa: D401 override
        try:
            if hasattr(self._monitor, "stop_monitoring") and self._running:
                self._monitor.stop_monitoring()
        finally:
            super().destroy()
