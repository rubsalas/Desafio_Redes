# Monitor de Red con RESTCONF y YANG

Este es el Trabajo Final del curso CE-5301 Redes de Computadores del Programa de Ingeniería en Computadores del Instituto Tecnológico de Costa Rica, Semestre I 2025. El proyecto explora la programabilidad basada en modelos mediante el uso de RESTCONF y modelos YANG aplicados al monitoreo de redes modernas sobre infraestructura Cisco.

## Características Principales

* Monitoreo continuo de interfaces de red
* Detección de fallas y anomalías mediante alertas inteligentes
* Recolección de estadísticas de red mediante RESTCONF
* Generación periódica de reportes (JSON y visuales)
* Basado en estándares abiertos: RESTCONF, YANG
* Adaptado a formato de referencia CatalystData.json

## Configuración Básica

```python
BASE_URL = "https://sandbox-iosxe-latest-1.cisco.com/restconf/data"

HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
    "Authorization": "Basic ZGV2ZWxvcGVyOkMxc2NvMTIzNDU="
}
```

## Modelos de Datos

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

@dataclass
class Alert:
    type: str
    message: str
    severity: str
    timestamp: str
    interface: Optional[str] = None
```

## Estructura del Monitor

### 1. Inicialización y Control

```python
def start_monitoring(self):
def stop_monitoring(self):
def _monitoring_loop(self):
```

* Ejecuta la actualización periódica en un hilo separado

### 2. Recolección de Datos

```python
def fetch_interfaces(self):
def fetch_interface_stats(self, interface_name: str):
```

* Llama a los endpoints RESTCONF para `ietf-interfaces` y `interfaces-state`
* Estructura los datos en objetos definidos por YANG

### 3. Detección de Alertas

```python
def check_for_alerts(self):
```

* Detecta interfaces caídas, sin IP o con errores excesivos

### 4. Histórico y Reportes

```python
def update_history(self):
def generate_reports(self):
def generate_interfaces_table(self):
def generate_bandwidth_report(self):
def generate_alerts_report(self):
```

* Mantiene un historial acotado por `HISTORY_LIMIT`
* Genera reportes JSON y un gráfico de ancho de banda

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

* `interfaces_table.json`: Tabla con estado y atributos de interfaces
* `bandwidth_history.png`: Gráfico del uso de ancho de banda
* `alerts_report.json`: Reporte de alertas activas

## Variables de Configuración

* `POLLING_INTERVAL`: Intervalo entre recolecciones (segundos)
* `HISTORY_LIMIT`: Límite del historial de puntos
* `bandwidth_threshold`: Umbral de alerta por uso
* `error_threshold`: Umbral de alerta por errores
