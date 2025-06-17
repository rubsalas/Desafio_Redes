
# Network Device Monitor (Cisco DNA RESTCONF)

Este script en Python implementa un sistema de monitoreo en tiempo real para dispositivos de red usando la API RESTCONF de Cisco DNA Center. Extrae información de dispositivos, genera reportes periódicos, detecta alertas críticas y guarda datos históricos de rendimiento.

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

## Seguridad

El script desactiva la verificación SSL (`verify=False`) para evitar errores con certificados autofirmados. Se recomienda usar en entornos controlados o adaptar para validar certificados.

