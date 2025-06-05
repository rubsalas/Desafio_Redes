# Desafio_Redes
Este es el Trabajo Final del curso CE-5301 Redes de Computadores del Programa de Ingeniería en Computadores del Instituto Tecnológico de Costa Rica para el Semestre I 2025. El Desafío de Redes donde se investigará sobre los fundamentos de programabilidad basada en modelos y cómo aplicar un caso de uso específico de llamadas REST en redes modernas.

# Monitor de Red con RESTCONF y YANG

Este proyecto implementa un sistema de monitoreo de red que utiliza RESTCONF y modelos YANG para recolectar datos de dispositivos de red Cisco (usando Cisco Sandbox). El sistema se ejecuta continuamente, recolectando datos periódicamente y generando reportes para su visualización.

## Características Principales

- Monitoreo continuo de interfaces de red
- Detección automática de problemas (alertas)
- Generación de reportes en formato JSON e imágenes
- Histórico de métricas para análisis de tendencias
- Basado en estándares abiertos (RESTCONF, YANG)

## Estructura del Código

### 1. Configuración Inicial

# Configuración básica
```python
BASE_URL = "https://sandbox-iosxe-latest-1.cisco.com/restconf/data"

HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
    "Authorization": "Basic ZGV2ZWxvcGVyOkMxc2NvMTIzNDU="
}
```
BASE_URL: Endpoint base para las API RESTCONF

HEADERS: Configuración de cabeceras HTTP necesarias para autenticación y formato de datos


### 2. Modelos de Datos
Clases que representan los modelos YANG:
```python
@dataclass
class InterfaceIP:
    ip: str
    netmask: str

@dataclass
class InterfaceStats:
    in_octets: int
    out_octets: int
    in_errors: int
    out_errors: int
    last_updated: str

@dataclass
class Interface:
    name: str
    description: str
    enabled: bool
    oper_status: str
    ipv4: Optional[InterfaceIP] = None
    ipv6: Optional[InterfaceIP] = None
    speed: Optional[int] = None
    stats: Optional[InterfaceStats] = None
```

### 3. Clase Principal NetworkMonitor
El núcleo del sistema con estos componentes principales:

## a. Inicialización y Control

```python
def start_monitoring(self):
def stop_monitoring(self):
def _monitoring_loop(self):
```
Controla el ciclo de vida del monitoreo

Ejecuta en un hilo separado para no bloquear la aplicación principal

## b. Recolección de Datos

```python
def fetch_interfaces(self):
def fetch_interface_stats(self, interface_name: str):
```

Realiza llamadas RESTCONF para obtener datos

Parsea las respuestas JSON a los modelos de datos

### c. Detección de Alertas

```python
def check_for_alerts(self):
```

Verifica condiciones anómalas (interfaces caídas, errores, etc.)

Genera objetos Alert cuando detecta problemas


## d. Histórico y Reportes

```python
def update_history(self):
def generate_reports(self):
def generate_interfaces_table(self):
def generate_bandwidth_report(self):
def generate_alerts_report(self):
```

Mantiene un historial de métricas para análisis temporal

Genera reportes en formatos consumibles por el frontend

### 4. Flujo Principal

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

interfaces_table.json - Contiene:
```json
[
  {
    "name": "GigabitEthernet1",
    "description": "Interface description",
    "status": "UP",
    "enabled": "Sí",
    "ip_info": "IPv4: 10.10.20.148/255.255.255.0",
    "speed": "1000 Mbps"
  }
]
```
bandwidth_history.png - Gráfico de tendencia de uso de ancho de banda

alerts_report.json - Listado de alertas activas:

```json
[
  {
    "timestamp": "2023-11-15 14:30:45",
    "severity": "critical",
    "message": "La interfaz GigabitEthernet2 está deshabilitada",
    "interface": "GigabitEthernet2"
  }
]
```
### Variables de Configuración Importantes

POLLING_INTERVAL: Tiempo entre actualizaciones (en segundos)

HISTORY_LIMIT: Límite de puntos en el historial

bandwidth_threshold: Umbral para alertas de ancho de banda

error_threshold: Umbral para alertas de errores

