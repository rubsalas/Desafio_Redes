# Network Device Monitor (Cisco DNA RESTCONF)

Este script en Python implementa un sistema de monitoreo en tiempo real para dispositivos de red usando la API RESTCONF de Cisco DNA Center. Extrae información de dispositivos, genera reportes periódicos, detecta alertas críticas y guarda datos históricos de rendimiento.

- Monitoreo continuo de interfaces de red
- Detección de fallas y anomalías mediante alertas inteligentes
- Recolección de estadísticas de red mediante RESTCONF
- Generación periódica de reportes (JSON y visuales)
- Basado en estándares abiertos: RESTCONF, YANG
- # Adaptado a formato de referencia CatalystData.json

## Funcionalidades

- Consulta periódica de dispositivos de red mediante Cisco DNA RESTCONF.
- Almacenamiento histórico de métricas por dispositivo.
- Detección automática de alertas:
  - Dispositivos no alcanzables.
  - Dispositivos no soportados.
  - Problemas en la recolección de datos.
  - Reinicios recientes.
- Generación de reportes automáticos:
  - Tabla de dispositivos (`devices_table.json`).
  - Reporte de alcanzabilidad histórica (`reachability_history.png`).
  - Alertas activas (`alerts_report.json`).

## Requisitos

- Python 3.7 o superior
- Acceso a Cisco DNA Center con RESTCONF habilitado
- Token de autenticación válido para la API

## Instalación

Ejecuta el siguiente comando para instalar las dependencias necesarias:

```bash
pip install requests matplotlib
```

## Configuración

Antes de ejecutar el script, edita las variables en el código:

- `BASE_URL`: URL base de la API RESTCONF de Cisco DNA Center.
- `HEADERS`: encabezados HTTP, incluyendo el token en `X-Auth-Token`.

Opcionalmente, puedes modificar:

- `POLLING_INTERVAL`: intervalo en segundos entre cada consulta (por defecto 60).
- `HISTORY_LIMIT`: cantidad máxima de registros históricos por dispositivo.

## Uso

Para iniciar el monitor, ejecuta:

```bash
python monitor.py
```

El monitor se ejecutará indefinidamente hasta que presiones `Ctrl + C` para detenerlo.

## Archivos generados

- `devices_table.json`: contiene una tabla con información actualizada de dispositivos.
- `alerts_report.json`: reporte con alertas detectadas en el último ciclo.
- `reachability_history.png`: gráfico con el estado histórico de alcanzabilidad por dispositivo.

- # Ejecuta la actualización periódica en un hilo separado

## Seguridad

El script desactiva la verificación SSL (`verify=False`) para evitar errores con certificados autofirmados. Se recomienda usar en entornos controlados o adaptar para validar certificados.

```python
def fetch_interfaces(self):
def fetch_interface_stats(self, interface_name: str):
```

- Llama a los endpoints RESTCONF para `ietf-interfaces` y `interfaces-state`
- Estructura los datos en objetos definidos por YANG

### 3. Detección de Alertas

```python
def check_for_alerts(self):
```

- Detecta interfaces caídas, sin IP o con errores excesivos

### 4. Histórico y Reportes

```python
def update_history(self):
def generate_reports(self):
def generate_interfaces_table(self):
def generate_bandwidth_report(self):
def generate_alerts_report(self):
```

- Mantiene un historial acotado por `HISTORY_LIMIT`
- Genera reportes JSON y un gráfico de ancho de banda

### 5. Ejecución Principal

```python
def main():
    monitor = NetworkMonitor()
    monitor.start_monitoring()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
```

## Archivos Generados

- `interfaces_table.json`: Tabla con estado y atributos de interfaces
- `bandwidth_history.png`: Gráfico del uso de ancho de banda
- `alerts_report.json`: Reporte de alertas activas

## Variables de Configuración

- `POLLING_INTERVAL`: Intervalo entre recolecciones (segundos)
- `HISTORY_LIMIT`: Límite del historial de puntos
- `bandwidth_threshold`: Umbral de alerta por uso
- `error_threshold`: Umbral de alerta por errores

## Monitor Application

A minimal, **cleanly‑layered** desktop application built with Tkinter and Matplotlib.
The code base is split into _UI_ and _business‑logic_ modules so the project can scale without turning it into a monolith.

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

- Python ≥ 3.9 (Linux, macOS or Windows)
- Tk headers (usually pre‑installed with Python)
- `pip install matplotlib numpy`

#### 2 – Run the program

```bash
# clone your own repo / copy the files
cd Program

pip install matplotlib numpy

python main.py                # launches the GUI
```
