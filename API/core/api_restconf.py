import os
import threading
from typing import List, Dict, Optional
from datetime import datetime
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
import uvicorn
import pyang
from pyang.repository import FileRepository
from network_monitor import NetworkMonitor, Alert

# Configuración de la aplicación FastAPI
app = fastapi.FastAPI(
    title="Network Monitor RESTCONF API",
    description="API RESTCONF para el sistema de monitoreo de red con validación YANG",
    version="2.0.0",
    servers=[{"url": "http://localhost:8000", "description": "Local development server"}],
    openapi_tags=[{
        "name": "network-monitor",
        "description": "Endpoints para monitoreo de red con soporte RESTCONF/YANG"
    }]
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de modelos YANG
YANG_MODELS_DIR = os.path.join(os.path.dirname(__file__), "yang_models")
YANG_MODELS = [
    "ietf-yang-types.yang",
    "ietf-inet-types.yang",
    "network-monitor.yang",
    "network-monitor-extensions.yang"
]

# Instancia del monitor de red
monitor = NetworkMonitor()

class DeviceModel(BaseModel):
    id: str
    hostname: str
    managementIpAddress: str
    macAddress: str
    softwareVersion: str
    reachabilityStatus: str
    upTime: str
    serialNumber: str
    platformId: str
    interfaceCount: int
    lastUpdated: str
    description: Optional[str] = None
    role: Optional[str] = None
    vendor: Optional[str] = None
    type: Optional[str] = None
    family: Optional[str] = None
    series: Optional[str] = None
    softwareType: Optional[str] = None
    deviceSupportLevel: Optional[str] = None
    collectionStatus: Optional[str] = None
    bootDateTime: Optional[str] = None

    class Config:
        json_schema_extra = {
            "yang-type": "list",
            "yang-module": "network-devices",
            "yang-path": "/devices/device"
        }

    @field_validator('interfaceCount', mode='before')
    def parse_interface_count(cls, v):
        return int(v) if str(v).isdigit() else 0

class AlertModel(BaseModel):
    type: str
    message: str
    severity: str
    timestamp: str
    device_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "yang-type": "list",
            "yang-module": "network-alerts",
            "yang-path": "alerts/alert"
        }

class HistoryPointModel(BaseModel):
    timestamp: str
    reachability: str
    uptime: str
    interface_count: int
    software_version: str

    class Config:
        json_schema_extra = {
            "yang-type": "list",
            "yang-module": "network-history",
            "yang-path": "/device-history/point"
        }

class MonitorConfigModel(BaseModel):
    polling_interval: int
    history_limit: int
    running: bool

    class Config:
        json_schema_extra = {
            "yang-type": "container",
            "yang-module": "network-monitor",
            "yang-path": "/monitor-config"
        }

# Iniciar el monitor en segundo plano
monitor_thread = threading.Thread(target=monitor.start_monitoring)
monitor_thread.daemon = True
monitor_thread.start()

## Endpoints de Dispositivos
@app.get("/restconf/data/network-devices:devices", 
         response_model=List[DeviceModel],
         tags=["devices"])
def get_devices():
    """Obtener todos los dispositivos monitoreados"""
    if not monitor.devices:
        if not monitor.fetch_devices():
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudieron obtener los dispositivos"
            )
    return monitor.devices

@app.get("/restconf/data/network-devices:devices/device={device_id}", 
         response_model=DeviceModel,
         tags=["devices"])
def get_device(device_id: str):
    """Obtener un dispositivo específico"""
    device = next((d for d in monitor.devices if d.id == device_id), None)
    if not device:
        raise fastapi.HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return device

@app.get("/restconf/data/network-devices:device-history/device={device_id}", 
         response_model=List[HistoryPointModel],
         tags=["devices"])
def get_device_history(device_id: str):
    """Obtener historial de un dispositivo"""
    if device_id not in monitor.device_history:
        raise fastapi.HTTPException(status_code=404, detail="Historial no encontrado")
    return monitor.device_history[device_id]

## Endpoints de Alertas
@app.get("/restconf/data/network-alerts:alerts", 
         response_model=List[AlertModel],
         tags=["alerts"])
def get_alerts():
    """Obtener todas las alertas activas"""
    return monitor.alerts

## Endpoints de Control
@app.get("/restconf/data/network-monitor:status", 
         response_model=MonitorConfigModel,
         tags=["monitor"])
def get_monitor_status():
    """Obtener estado del monitor"""
    return {
        "polling_interval": monitor.polling_interval,
        "history_limit": monitor.history_limit,
        "running": monitor.running
    }

@app.post("/restconf/data/network-monitor:update", 
          tags=["monitor"])
def force_update():
    """Forzar actualización de datos"""
    monitor.fetch_devices()
    return {"message": "Actualización forzada iniciada"}

@app.put("/restconf/data/network-monitor:config", 
         response_model=MonitorConfigModel,
         tags=["monitor"])
def update_config(config: MonitorConfigModel):
    """Actualizar configuración del monitor"""
    monitor.polling_interval = config.polling_interval
    monitor.history_limit = config.history_limit
    
    if config.running and not monitor.running:
        monitor.start_monitoring()
    elif not config.running and monitor.running:
        monitor.stop_monitoring()
    
    return get_monitor_status()


## Endpoint de descubrimiento RESTCONF
@app.get("/.well-known/host-meta", include_in_schema=False)
def get_host_meta():
    return JSONResponse(
        content={
            "XRD": {
                "@xmlns": "http://docs.oasis-open.org/ns/xri/xrd-1.0",
                "Link": [
                    {
                        "@rel": "restconf",
                        "@href": "/restconf"
                    }
                ]
            }
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )
