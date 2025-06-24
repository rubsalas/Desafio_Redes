# ui/app.py
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import re
from core.monitor_cli import NetworkMonitorCLI

# Título personalizado de la aplicación
titulo = "Custom Network Device Monitor (Cisco DNA RESTCONF)"

# Función helper para convertir camelCase a texto legible
def humanize(key):
    s = re.sub(r'(?<!^)(?=[A-Z])', ' ', key)
    return s.capitalize()

class NetworkMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(titulo)
        self.geometry("900x650")
        self.monitor = NetworkMonitorCLI()
        self.countdown = 15
        self.create_widgets()
        # Carga inicial sin bloquear UI
        self.refresh_devices()
        self.refresh_alerts()
        self.refresh_status()
        self.after(1000, self.update_timer)

    def create_widgets(self):
        # Header con indicador y título
        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=5)
        self.canvas_status = tk.Canvas(header, width=20, height=20, highlightthickness=0)
        self.canvas_status.pack(side="left", padx=(0,10))
        lbl_title = ttk.Label(header, text=titulo, font=(None, 16, 'bold'))
        lbl_title.pack(side="left")

        # Notebook para dispositivos
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=2)

        # Sección de alertas (Treeview original)
        alerts_frame = ttk.LabelFrame(self, text="Alertas")
        alerts_frame.pack(fill="both", expand=False, padx=10, pady=2)
        # Encabezado de alertas con contador
        alerts_header = ttk.Frame(alerts_frame)
        alerts_header.pack(fill="x", padx=5, pady=(5,0))
        lbl_alertas = ttk.Label(alerts_header, text="Alertas", font=(None, 12, 'bold'))
        lbl_alertas.pack(side="left")
        self.next_update_label = ttk.Label(alerts_header, text=f"Siguiente actualización: {self.countdown}s", font=(None,10))
        self.next_update_label.pack(side="left", padx=(20,0))
        # Tabla de alertas original
        cols2 = ("Tipo", "Mensaje", "Severidad", "Timestamp", "Interfaz")
        self.tree_alerts = ttk.Treeview(alerts_frame, columns=cols2, show="headings", height=5)
        for col in cols2:
            self.tree_alerts.heading(col, text=col)
            self.tree_alerts.column(col, width=150, anchor='w')
        self.tree_alerts.pack(fill="both", expand=True, padx=5, pady=5)

    def update_timer(self):
        if self.countdown > 0:
            self.next_update_label.config(text=f"Siguiente actualización: {self.countdown}s")
            self.countdown -= 1
        elif self.countdown == 0:
            self.next_update_label.config(text="Actualizando...")
            self._set_status_color('yellow')
            self.refresh_alerts()
            self.refresh_status()
            self.countdown = -1
        else:
            self.next_update_label.config(text="Actualizando...")
        self.after(1000, self.update_timer)

    def _set_status_color(self, color):
        self.canvas_status.delete("all")
        self.canvas_status.create_oval(2, 2, 18, 18, fill=color, outline=color)

    def refresh_status(self):
        def task():
            try:
                st = self.monitor.fetch_status()
                running = st.get('running', False)
                color = "green" if running else "red"
                self.after(0, lambda: self._set_status_color(color))
                self.after(0, lambda: setattr(self, 'countdown', 15))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error Estado", str(e)))
        threading.Thread(target=task, daemon=True).start()

    def refresh_alerts(self):
        def task():
            try:
                data = self.monitor.fetch_alerts()
                alerts = data if isinstance(data, list) else data.get('response', [])
                self.after(0, self._populate_alerts, alerts)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error Alertas", str(e)))
        threading.Thread(target=task, daemon=True).start()

    def _populate_alerts(self, alerts):
        for item in self.tree_alerts.get_children():
            self.tree_alerts.delete(item)
        for a in alerts:
            self.tree_alerts.insert("", "end", values=(
                a.get('type'),
                a.get('message'),
                a.get('severity'),
                a.get('timestamp'),
                a.get('interface'),
            ))

    def refresh_devices(self):
        def task():
            try:
                data = self.monitor.fetch_all_devices()
                devices = data if isinstance(data, list) else data.get('response', [])
                self.after(0, self._build_device_tabs, devices)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error Dispositivos", str(e)))
        threading.Thread(target=task, daemon=True).start()

    def _build_device_tabs(self, devices):
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        for d in devices:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=d.get('hostname'))
            table = ttk.Frame(frame)
            table.pack(fill="both", expand=True, padx=5, pady=5)
            # Encabezados de tabla con fondo gris claro
            tk.Label(table, text="Campo", borderwidth=1, relief="solid", bg="#cccccc", font=(None,10,'bold')).grid(row=0, column=0, sticky="nsew")
            tk.Label(table, text="Valor", borderwidth=1, relief="solid", bg="#cccccc", font=(None,10,'bold')).grid(row=0, column=1, sticky="nsew")
            table.columnconfigure(0, weight=1)
            table.columnconfigure(1, weight=2)
            # Filas de datos (sin 'description') con humanized keys
            row = 1
            for key, val in d.items():
                if key == 'description':
                    continue
                display_key = humanize(key)
                tk.Label(table, text=display_key, borderwidth=1, relief="solid", bg="#ffffff", anchor="w").grid(row=row, column=0, sticky="nsew")
                tk.Label(table, text=str(val), borderwidth=1, relief="solid", bg="#ffffff", anchor="w").grid(row=row, column=1, sticky="nsew")
                row += 1
        if devices:
            self.notebook.select(0)

if __name__ == '__main__':
    app = NetworkMonitorApp()
    app.mainloop()
