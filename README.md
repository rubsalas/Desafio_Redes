# Desafio_Redes
Este es el Trabajo Final del curso CE-5301 Redes de Computadores del Programa de Ingeniería en Computadores del Instituto Tecnológico de Costa Rica para el Semestre I 2025. El Desafío de Redes donde se investigará sobre los fundamentos de programabilidad basada en modelos y cómo aplicar un caso de uso específico de llamadas REST en redes modernas.


## Monitor Application

A minimal, **cleanly‑layered** desktop application built with Tkinter and Matplotlib.
The code base is split into *UI* and *business‑logic* modules so the project can scale without turning it into a monolith.

```
Program/
│
├─ main.py              # Entry point – wires UI ↔ logic and starts the event‑loop
│
├─ core/                # All non‑GUI, testable logic lives here
│   ├─ __init__.py
│   └─ monitor.py       # Class that serves data to the UI
│
└─ ui/                  # All Tkinter widgets and visual components
    ├─ __init__.py
    └─ app.py           # App(tk.Tk): window, frames, plots, callbacks
```


### Quick start

#### 1 – Prerequisites

* Python ≥ 3.9 (Linux, macOS or Windows)
* Tk headers (usually pre‑installed with Python)
* `pip install matplotlib numpy`


#### 2 – Run the program

```bash
# clone your own repo / copy the files
cd Program

pip install matplotlib numpy

python main.py                # launches the GUI
```

Future program explanation!

---
