# Desafío de Redes

## Sandbox

Descargar Cisco Secure Client

Conectarse al VPN.

Lab Network Address: http://devnetsandbox-usw1-reservation.cisco.com:20160

Ingresar usuario y contraseña.

## Network Device Monitor (Cisco DNA RESTCONF)

Se implementa un sistema de monitoreo en tiempo real para dispositivos de red usando la API RESTCONF de Cisco DNA Center. Con este se extrae información de dispositivos, genera reportes periódicos, detecta alertas críticas y guarda datos históricos de rendimiento.

- Monitoreo continuo de interfaces de red
- Detección de fallas y anomalías mediante alertas inteligentes
- Recolección de estadísticas de red mediante RESTCONF
- Generación periódica de reportes (JSON y visuales)
- Basado en estándares abiertos: RESTCONF, YANG
- Adaptado a formato de referencia CatalystData.json

### Funcionalidades

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

### Requisitos

- Python 3.7 o superior
- Acceso a Cisco DNA Center con RESTCONF habilitado
- Token de autenticación válido para la API

### Instalación

Ejecuta el siguiente comando para instalar las dependencias necesarias:

```bash
pip install requests matplotlib
```

### Configuración

Antes de ejecutar el script, edita las variables en el código:

- `BASE_URL`: URL base de la API RESTCONF de Cisco DNA Center.
- `HEADERS`: encabezados HTTP, incluyendo el token en `X-Auth-Token`.

Opcionalmente, puedes modificar:

- `POLLING_INTERVAL`: intervalo en segundos entre cada consulta (por defecto 60).
- `HISTORY_LIMIT`: cantidad máxima de registros históricos por dispositivo.

### Uso

Para iniciar el monitor, ejecuta:

```bash
python monitor.py
```

El monitor se ejecutará indefinidamente hasta que presiones `Ctrl + C` para detenerlo.

### Archivos generados

- `devices_table.json`: contiene una tabla con información actualizada de dispositivos.
- `alerts_report.json`: reporte con alertas detectadas en el último ciclo.
- `reachability_history.png`: gráfico con el estado histórico de alcanzabilidad por dispositivo.

- Ejecuta la actualización periódica en un hilo separado

### Seguridad

El script desactiva la verificación SSL (`verify=False`) para evitar errores con certificados autofirmados. Se recomienda usar en entornos controlados o adaptar para validar certificados.

```python
def fetch_interfaces(self):
def fetch_interface_stats(self, interface_name: str):
```

- Llama a los endpoints RESTCONF para `ietf-interfaces` y `interfaces-state`
- Estructura los datos en objetos definidos por YANG

### Detección de Alertas

```python
def check_for_alerts(self):
```

- Detecta interfaces caídas, sin IP o con errores excesivos

### Histórico y Reportes

```python
def update_history(self):
def generate_reports(self):
def generate_interfaces_table(self):
def generate_bandwidth_report(self):
def generate_alerts_report(self):
```

- Mantiene un historial acotado por `HISTORY_LIMIT`
- Genera reportes JSON y un gráfico de ancho de banda

### Ejecución Principal

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

### Archivos Generados

- `interfaces_table.json`: Tabla con estado y atributos de interfaces
- `bandwidth_history.png`: Gráfico del uso de ancho de banda
- `alerts_report.json`: Reporte de alertas activas

### Variables de Configuración

- `POLLING_INTERVAL`: Intervalo entre recolecciones (segundos)
- `HISTORY_LIMIT`: Límite del historial de puntos
- `bandwidth_threshold`: Umbral de alerta por uso
- `error_threshold`: Umbral de alerta por errores

## Network Monitor RESTCONF API Endpoints

1. Descargar e Instalar Cisco AnyConnect (VPN Client)

https://kb.itd.commonwealthu.edu/books/network/page/download-cisco-secure-client

pip install fastapi uvicorn pyang

Base URL: <http://localhost:8000/restconf/data>

### DEVICE ENDPOINTS

#### 1. Get all devices

`GET /network-devices:devices`
Headers:
`Accept: application/yang-data+json`

Example Response:

```json
{
  "id": "bfea531c-f8ff-476f-91c7-def7953b7706",
  "hostname": "sw1",
  "managementIpAddress": "10.10.20.175",
  "macAddress": "52:54:00:02:19:54",
  "softwareVersion": "17.12.1prd9",
  "reachabilityStatus": "Reachable",
  "upTime": "1 day, 0:09:19.00",
  "serialNumber": "CML12345UAD",
  "platformId": "C9KV-UADP-8P",
  "interfaceCount": 0,
  "lastUpdated": "2025-06-23 16:53:19",
  "description": "Cisco IOS Software [Dublin], Catalyst L3 Switch Software (CAT9K_IOSXE), Version 17.12.1prd9, RELEASE SOFTWARE (fc1) Technical Support: http://www.cisco.com/techsupport Copyright (c) 1986-2023 by Cisco Systems, Inc. Compiled Tue 15-Aug-23 16:44 by mcpre",
  "role": "ACCESS",
  "vendor": "Cisco",
  "type": "Cisco Catalyst 9000 UADP 8 Port Virtual Switch",
  "family": "Switches and Hubs",
  "series": "Cisco Catalyst 9000 Series Virtual Switches",
  "softwareType": "IOS-XE",
  "deviceSupportLevel": "Supported",
  "collectionStatus": "Managed",
  "bootDateTime": "2025-06-22 16:44:19"
},
{
  "id": "c6cd2772-05e7-41b0-b5cc-e7d1a3a86fc8",
  "hostname": "sw2",
  "managementIpAddress": "10.10.20.176",
  "macAddress": "52:54:00:07:29:d0",
  "softwareVersion": "17.12.1prd9",
  "reachabilityStatus": "Reachable",
  "upTime": "1 day, 0:09:08.00",
  "serialNumber": "CML12345",
  "platformId": "C9KV-UADP-8P",
  "interfaceCount": 0,
  "lastUpdated": "2025-06-23 16:53:11",
  "description": "Cisco IOS Software [Dublin], Catalyst L3 Switch Software (CAT9K_IOSXE), Version 17.12.1prd9, RELEASE SOFTWARE (fc1) Technical Support: http://www.cisco.com/techsupport Copyright (c) 1986-2023 by Cisco Systems, Inc. Compiled Tue 15-Aug-23 16:44 by mcpre",
  "role": "ACCESS",
  "vendor": "Cisco",
  "type": "Cisco Catalyst 9000 UADP 8 Port Virtual Switch",
  "family": "Switches and Hubs",
  "series": "Cisco Catalyst 9000 Series Virtual Switches",
  "softwareType": "IOS-XE",
  "deviceSupportLevel": "Supported",
  "collectionStatus": "Managed",
  "bootDateTime": "2025-06-22 16:44:11"
},
{
  "id": "322e2706-3c57-45fb-bb2d-ce91db3e38a6",
  "hostname": "sw3",
  "managementIpAddress": "10.10.20.177",
  "macAddress": "52:54:00:05:77:13",
  "softwareVersion": "17.12.1prd9",
  "reachabilityStatus": "Reachable",
  "upTime": "1 day, 0:09:15.00",
  "serialNumber": "CML12345ABC",
  "platformId": "C9KV-UADP-8P",
  "interfaceCount": 0,
  "lastUpdated": "2025-06-23 16:52:56",
  "description": "Cisco IOS Software [Dublin], Catalyst L3 Switch Software (CAT9K_IOSXE), Version 17.12.1prd9, RELEASE SOFTWARE (fc1) Technical Support: http://www.cisco.com/techsupport Copyright (c) 1986-2023 by Cisco Systems, Inc. Compiled Tue 15-Aug-23 16:44 by mcpre",
  "role": "ACCESS",
  "vendor": "Cisco",
  "type": "Cisco Catalyst 9000 UADP 8 Port Virtual Switch",
  "family": "Switches and Hubs",
  "series": "Cisco Catalyst 9000 Series Virtual Switches",
  "softwareType": "IOS-XE",
  "deviceSupportLevel": "Supported",
  "collectionStatus": "Managed",
  "bootDateTime": "2025-06-22 16:43:57"
},
{
  "id": "19423f63-ee4f-44dc-bbf6-240586297ed2",
  "hostname": "sw4",
  "managementIpAddress": "10.10.20.178",
  "macAddress": "52:54:00:0f:1c:07",
  "softwareVersion": "17.12.1prd9",
  "reachabilityStatus": "Reachable",
  "upTime": "1 day, 0:09:03.00",
  "serialNumber": "CML54321",
  "platformId": "C9KV-UADP-8P",
  "interfaceCount": 0,
  "lastUpdated": "2025-06-23 16:52:57",
  "description": "Cisco IOS Software [Dublin], Catalyst L3 Switch Software (CAT9K_IOSXE), Version 17.12.1prd9, RELEASE SOFTWARE (fc1) Technical Support: http://www.cisco.com/techsupport Copyright (c) 1986-2023 by Cisco Systems, Inc. Compiled Tue 15-Aug-23 16:44 by mcpre",
  "role": "ACCESS",
  "vendor": "Cisco",
  "type": "Cisco Catalyst 9000 UADP 8 Port Virtual Switch",
  "family": "Switches and Hubs",
  "series": "Cisco Catalyst 9000 Series Virtual Switches",
  "softwareType": "IOS-XE",
  "deviceSupportLevel": "Supported",
  "collectionStatus": "Managed",
  "bootDateTime": "2025-06-22 16:43:57"
}
```

#### 2. Get single device

`GET /network-devices:devices/device={device_id}`
Params:
`device_id: string (UUID)`

Example Response:

```json
{
  "id": "bfea531c-f8ff-476f-91c7-def7953b7706",
  "hostname": "sw1",
  "managementIpAddress": "10.10.20.175",
  "macAddress": "52:54:00:02:19:54",
  "softwareVersion": "17.12.1prd9",
  "reachabilityStatus": "Reachable",
  "upTime": "1 day, 0:09:19.00",
  "serialNumber": "CML12345UAD",
  "platformId": "C9KV-UADP-8P",
  "interfaceCount": 0,
  "lastUpdated": "2025-06-23 16:53:19",
  "description": "Cisco IOS Software [Dublin], Catalyst L3 Switch Software (CAT9K_IOSXE), Version 17.12.1prd9, RELEASE SOFTWARE (fc1) Technical Support: http://www.cisco.com/techsupport Copyright (c) 1986-2023 by Cisco Systems, Inc. Compiled Tue 15-Aug-23 16:44 by mcpre",
  "role": "ACCESS",
  "vendor": "Cisco",
  "type": "Cisco Catalyst 9000 UADP 8 Port Virtual Switch",
  "family": "Switches and Hubs",
  "series": "Cisco Catalyst 9000 Series Virtual Switches",
  "softwareType": "IOS-XE",
  "deviceSupportLevel": "Supported",
  "collectionStatus": "Managed",
  "bootDateTime": "2025-06-22 16:44:19"
}
```

#### 3. Get device history

`GET /network-devices:device-history/device={device_id}`
Params:
`device_id: string (UUID)`

Example Response:

```json
{
  "timestamp": "2025-06-24T01:57:50.466134",
  "reachability": "Reachable",
  "uptime": "1 day, 0:09:19.00",
  "interface_count": 0,
  "software_version": "17.12.1prd9"
}
```

### ALERT ENDPOINTS

#### 4. Get all alerts

`GET /network-alerts:alerts`

Example Response: (?)

```json
{
  "type": "INTERFACE_DOWN",
  "message": "Interface GigabitEthernet2 is down",
  "severity": "critical",
  "timestamp": "2025-06-16T14:31:22",
  "interface": "GigabitEthernet2"
}
```

### MONITOR

#### 5. Get monitor status

`GET /network-monitor:status`

Example Response: (?)

```json
{
  "polling_interval": 15,
  "history_limit": 1440,
  "running": true
}
```

## Monitor Application

A minimal, cleanly‑layered desktop application built with Tkinter and Matplotlib.
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

for client

pip install requests
