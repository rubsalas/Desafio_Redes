"""
ui/app.py – GUI
=============================================

Interfaz completa con:
* Barra superior: título, estado, botones *Start/Stop* y hora del último snapshot.
* Pestañas: tabla de interfaces y gráfico de ancho de banda en tiempo real.
* Panel inferior: lista de alertas.

La aplicación recibe instantáneas de un objeto monitor
mediante un callback thread-safe y actualiza los widgets usando
`queue.Queue + after()`.
"""
from __future__ import annotations

import queue
import tkinter as tk
from datetime import datetime
from typing import Any, Dict, List, Tuple

import matplotlib
import numpy as np
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

matplotlib.use("TkAgg")  # backend Tkinter

__all__ = ["App"]

# ───────────────────────────────────────────────────────────────────────────────
# Frames especializados
# ───────────────────────────────────────────────────────────────────────────────


class TopBar(ttk.Frame):
    """Encabezado con título, estado del monitor y botones."""

    def __init__(self, master: tk.Misc, *, start_cb, stop_cb) -> None:  # type: ignore[name-defined]
        super().__init__(master, padding=8)

        self._start_cb = start_cb
        self._stop_cb = stop_cb

        self.columnconfigure(2, weight=1)

        ttk.Label(self, text="Desafío Redes", font=("Helvetica", 18, "bold")).grid(
            row=0, column=0, sticky="w"
        )

        # LED de estado (● rojo/verde)
        self._led = ttk.Label(self, text="●", foreground="red", font=("Helvetica", 14))
        self._led.grid(row=0, column=1, padx=6)

        # Última hora
        self._lbl_time = ttk.Label(self, text="—")
        self._lbl_time.grid(row=0, column=2, sticky="e", padx=6)

        self._btn_start = ttk.Button(self, text="Start", command=self._start)
        self._btn_start.grid(row=0, column=3, padx=(6, 3))
        self._btn_stop = ttk.Button(self, text="Stop", command=self._stop, state="disabled")
        self._btn_stop.grid(row=0, column=4, padx=(3, 6))

    # ── API pública ───────────────────────────────────────────────────────────
    def set_running(self, running: bool) -> None:
        self._led.configure(foreground="green" if running else "red")
        self._btn_start.configure(state="disabled" if running else "normal")
        self._btn_stop.configure(state="normal" if running else "disabled")

    def set_timestamp(self, ts: str) -> None:
        self._lbl_time.configure(text=ts)

    # ── callbacks internos ────────────────────────────────────────────────────
    def _start(self):
        self._start_cb()

    def _stop(self):
        self._stop_cb()


class InterfacesFrame(ttk.Frame):
    """Tabla con inventario de interfaces."""

    COLS = ("name", "status", "ip", "speed", "description")

    def __init__(self, master: tk.Misc, *, on_select) -> None:  # type: ignore[name-defined]
        super().__init__(master, padding=10)
        self._tree = ttk.Treeview(self, columns=self.COLS, show="headings", height=12)
        self._tree.pack(fill="both", expand=True)

        headers = {
            "name": "Interface",
            "status": "Status",
            "ip": "IP Address",
            "speed": "Mb/s",
            "description": "Description",
        }
        for col in self.COLS:
            self._tree.heading(col, text=headers[col])
            self._tree.column(col, anchor="center")

        # Colores de fila según estado
        self._tree.tag_configure("up", background="#d7f8d7")
        self._tree.tag_configure("down", background="#f8d7d7")

        self._tree.bind("<<TreeviewSelect>>", lambda e: self._on_select(on_select))

    def _on_select(self, cb):
        sel = self._tree.selection()
        if sel:
            iid = sel[0]
            iface = self._tree.item(iid, "values")[0]
            cb(iface)

    # API
    def update(self, interfaces: Dict[str, Dict[str, Any]]):
        self._tree.delete(*self._tree.get_children())
        for intf in interfaces.values():
            status = intf.get("status", "down")
            self._tree.insert(
                "",
                "end",
                values=(
                    intf["name"],
                    status,
                    intf.get("ip", "—"),
                    intf.get("speed", "—"),
                    intf.get("description", ""),
                ),
                tags=(status,),
            )


class BandwidthFrame(ttk.Frame):
    """Gráfico de uso de ancho de banda para una interfaz."""

    def __init__(self, master: tk.Misc):  # type: ignore[name-defined]
        super().__init__(master, padding=10)
        self._fig = Figure(figsize=(5, 3), dpi=100)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_ylabel("% BW usage")
        self._ax.set_ylim(0, 100)
        self._line = None
        self._selected: str | None = None

        canvas = FigureCanvasTkAgg(self._fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvas = canvas

    def select_interface(self, name: str):
        self._selected = name
        self._ax.clear()
        self._ax.set_title(f"Bandwidth – {name}")
        self._ax.set_ylabel("% BW usage")
        self._ax.set_ylim(0, 100)
        self._line = None
        self._canvas.draw_idle()

    def update_history(self, history: Dict[str, List[Tuple[str, float]]]):
        if not self._selected or self._selected not in history:
            return
        data = history[self._selected][-60:]  # últimos 60 puntos
        if not data:
            return
        x_labels = [ts.split("T")[1] for ts, _ in data]
        y = [v for _, v in data]
        x = np.arange(len(y))
        if self._line is None:
            (self._line,) = self._ax.plot(x, y, "-o")
        else:
            self._line.set_data(x, y)
        self._ax.set_xticks(x[:: max(1, len(x) // 8)])
        self._ax.set_xticklabels(x_labels[:: max(1, len(x_labels) // 8)], rotation=45, ha="right", fontsize=7)
        self._ax.set_xlim(0, len(x) - 1)
        self._ax.set_ylim(0, 100)
        self._canvas.draw_idle()


class AlertsFrame(ttk.Frame):
    """Lista de alertas con severidad."""

    COLS = ("time", "severity", "interface", "message")

    def __init__(self, master: tk.Misc):  # type: ignore[name-defined]
        super().__init__(master, padding=10)
        self._tree = ttk.Treeview(self, columns=self.COLS, show="headings", height=6)
        self._tree.pack(fill="both", expand=True)

        headers = {
            "time": "Time",
            "severity": "Severity",
            "interface": "Iface",
            "message": "Message",
        }
        for col in self.COLS:
            self._tree.heading(col, text=headers[col])
            self._tree.column(col, anchor="center")

    def update(self, alerts: List[Dict[str, Any]]):
        self._tree.delete(*self._tree.get_children())
        for alert in alerts[-100:]:
            self._tree.insert(
                "",
                "end",
                values=(
                    alert["timestamp"].split("T")[1],
                    alert["severity"],
                    alert.get("interface", ""),
                    alert["message"],
                ),
            )


# ───────────────────────────────────────────────────────────────────────────────
# Aplicación principal
# ───────────────────────────────────────────────────────────────────────────────


class App(tk.Tk):
    """Capa de orquestación entre Monitor y Frames Tkinter."""

    POLL_MS = 500

    def __init__(self, monitor: Any):
        super().__init__()
        self.title("Desafío Redes")
        self.geometry("960x720")
        self.minsize(800, 600)

        # ── dependencias
        self._monitor = monitor
        self._q_snap: queue.Queue[dict] = queue.Queue()
        if hasattr(self._monitor, "on_update"):
            self._monitor.on_update = self._q_snap.put  # type: ignore

        self._running = False
        self._selected_iface: str | None = None

        # ── construir layout
        self._build()
        self.after(self.POLL_MS, self._drain_queue)

    # ────────────────────────────── layout ────────────────────────────────
    def _build(self):
        # Barra superior
        self._top = TopBar(self, start_cb=self._start, stop_cb=self._stop)
        self._top.pack(fill="x")

        # Notebook central
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self._f_int = InterfacesFrame(nb, on_select=self._select_iface)
        nb.add(self._f_int, text="Interfaces")

        self._f_bw = BandwidthFrame(nb)
        nb.add(self._f_bw, text="Bandwidth")

        # Panel de alertas
        self._f_alerts = AlertsFrame(self)
        self._f_alerts.pack(fill="both")

    # ───────────────────── control del monitor ────────────────────────────
    def _start(self):
        if self._running:
            return
        if hasattr(self._monitor, "start_monitoring"):
            self._monitor.start_monitoring()
        self._running = True
        self._top.set_running(True)

    def _stop(self):
        if not self._running:
            return
        if hasattr(self._monitor, "stop_monitoring"):
            self._monitor.stop_monitoring()
        self._running = False
        self._top.set_running(False)

    # ────────────────────────── cola / snapshots ──────────────────────────
    def _drain_queue(self):
        try:
            while True:
                snap = self._q_snap.get_nowait()
                self._process_snap(snap)
        except queue.Empty:
            pass
        self.after(self.POLL_MS, self._drain_queue)

    def _process_snap(self, snap: dict):
        ts = snap.get("timestamp") or datetime.utcnow().isoformat(timespec="seconds")
        self._top.set_timestamp(ts.split("T")[1])

        # Tabla de interfaces
        self._f_int.update(snap.get("interfaces", {}))

        # Selección inicial de interfaz si no hay una
        if self._selected_iface is None and snap.get("interfaces"):
            self._selected_iface = next(iter(snap["interfaces"].keys()))
            self._f_bw.select_interface(self._selected_iface)

        # Update gráfico BW
        self._f_bw.update_history(snap.get("bandwidth_history", {}))

        # Alertas
        self._f_alerts.update(snap.get("alerts", []))

    # ─────────────────────────── callbacks UI ─────────────────────────────
    def _select_iface(self, name: str):
        self._selected_iface = name
        self._f_bw.select_interface(name)

    # ───────────────────────────── limpiar ────────────────────────────────
    def destroy(self):  # noqa: D401 override
        try:
            if hasattr(self._monitor, "stop_monitoring"):
                self._monitor.stop_monitoring()
        finally:
            super().destroy()
