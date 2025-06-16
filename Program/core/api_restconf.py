import os
import threading
from typing import List, Dict, Optional
from datetime import datetime
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import pyang
from pyang.repository import FileRepository
from network_monitor import NetworkMonitor, Interface, Alert

# Configuración de la aplicación FastAPI
app = fastapi.FastAPI(
    title="Network Monitor RESTCONF API",
    description="API RESTCONF para el sistema de monitoreo de red con validación YANG",
    version="1.0.0",
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

# Modelos Pydantic para la API
class InterfaceIPModel(BaseModel):
    ip: str
    netmask: str

    class Config:
        json_schema_extra = {
            "yang-type": "grouping",
            "yang-module": "network-monitor",
            "yang-grouping": "interface-ip-grouping"
        }

class InterfaceStatsModel(BaseModel):
    in_octets: int
    out_octets: int
    in_errors: int
    out_errors: int
    last_updated: str

    class Config:
        json_schema_extra = {
            "yang-type": "grouping",
            "yang-module": "network-monitor",
            "yang-grouping": "interface-stats-grouping"
        }

class InterfaceModel(BaseModel):
    name: str
    description: str
    enabled: bool
    oper_status: str
    ipv4: Optional[InterfaceIPModel] = None
    ipv6: Optional[InterfaceIPModel] = None
    speed: Optional[int] = None
    stats: Optional[InterfaceStatsModel] = None

    class Config:
        json_schema_extra = {
            "yang-type": "list",
            "yang-module": "network-monitor",
            "yang-path": "/interfaces/interface"
        }

class AlertModel(BaseModel):
    type: str
    message: str
    severity: str
    timestamp: str
    interface: Optional[str] = None

    class Config:
        json_schema_extra = {
            "yang-type": "grouping",
            "yang-module": "network-monitor",
            "yang-grouping": "alert-grouping"
        }

class BandwidthHistoryPoint(BaseModel):
    timestamp: str
    value: float

    class Config:
        json_schema_extra = {
            "yang-type": "grouping",
            "yang-module": "network-monitor",
            "yang-grouping": "history-point-grouping"
        }

class ErrorHistoryPoint(BaseModel):
    timestamp: str
    value: int

    class Config:
        json_schema_extra = {
            "yang-type": "grouping",
            "yang-module": "network-monitor",
            "yang-grouping": "history-point-grouping"
        }

class MonitorConfigModel(BaseModel):
    polling_interval: int
    bandwidth_threshold: float
    error_threshold: int
    running: bool
    history_limit: Optional[int] = 1440
    alert_retention: Optional[int] = 24

    class Config:
        json_schema_extra = {
            "yang-type": "container",
            "yang-module": "network-monitor",
            "yang-path": "/monitor-config"
        }

class UpdateResponse(BaseModel):
    result: str

    class Config:
        json_schema_extra = {
            "yang-type": "rpc-output",
            "yang-module": "network-monitor",
            "yang-rpc": "force-update"
        }

# Funciones de validación YANG
def validate_with_yang(data, model_name, path=None):
    """Valida los datos contra un modelo YANG específico"""
    try:
        ctx = pyang.Context()
        repo = FileRepository(YANG_MODELS_DIR)
        ctx.add_module_repository(repo)
        
        for model in YANG_MODELS:
            ctx.add_module(model.split('.')[0])
        
        module = ctx.get_module(model_name)
        if not module:
            raise ValueError(f"Modelo YANG {model_name} no encontrado")
        
        # En una implementación real, aquí iría la validación detallada
        # usando pyangbind o similar para validar la estructura completa
        
        return True
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en validación YANG: {str(e)}"
        )

# Iniciar el monitor en segundo plano
monitor_thread = threading.Thread(target=monitor.start_monitoring)
monitor_thread.daemon = True
monitor_thread.start()

# Endpoints de la API
@app.get("/restconf/data/network-monitor:interfaces", 
         response_model=List[InterfaceModel],
         tags=["network-monitor"])
def get_interfaces():
    """Obtener lista de todas las interfaces de red"""
    if not validate_with_yang(monitor.interfaces, "network-monitor", "/interfaces"):
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Los datos no cumplen con el modelo YANG"
        )
    return monitor.interfaces

@app.get("/restconf/data/network-monitor:interfaces/interface={interface_name}", 
         response_model=InterfaceModel,
         tags=["network-monitor"])
def get_interface(interface_name: str):
    """Obtener información detallada de una interfaz específica"""
    for interface in monitor.interfaces:
        if interface.name == interface_name:
            if not validate_with_yang(interface, "network-monitor", f"/interfaces/interface={interface_name}"):
                raise fastapi.HTTPException(
                    status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Los datos no cumplen con el modelo YANG"
                )
            return interface
    raise fastapi.HTTPException(status_code=404, detail="Interfaz no encontrada")

@app.get("/restconf/data/network-monitor:alerts", 
         response_model=List[AlertModel],
         tags=["network-monitor"])
def get_alerts():
    """Obtener todas las alertas actuales"""
    if not validate_with_yang(monitor.alerts, "network-monitor", "/alerts"):
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Los datos no cumplen con el modelo YANG"
        )
    return monitor.alerts

@app.get("/restconf/data/network-monitor:bandwidth-history", 
         response_model=Dict[str, List[BandwidthHistoryPoint]],
         tags=["network-monitor"])
def get_bandwidth_history():
    """Obtener el historial de uso de ancho de banda por interfaz"""
    if not validate_with_yang(monitor.bandwidth_history, "network-monitor", "/bandwidth-history"):
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Los datos no cumplen con el modelo YANG"
        )
    return monitor.bandwidth_history

@app.get("/restconf/data/network-monitor:error-history", 
         response_model=Dict[str, List[ErrorHistoryPoint]],
         tags=["network-monitor"])
def get_error_history():
    """Obtener el historial de errores por interfaz"""
    if not validate_with_yang(monitor.error_history, "network-monitor", "/error-history"):
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Los datos no cumplen con el modelo YANG"
        )
    return monitor.error_history

@app.get("/restconf/data/network-monitor:status", 
         response_model=MonitorConfigModel,
         tags=["network-monitor"])
def get_monitor_status():
    """Obtener el estado actual del monitor"""
    status_data = {
        "polling_interval": monitor.polling_interval,
        "bandwidth_threshold": monitor.bandwidth_threshold,
        "error_threshold": monitor.error_threshold,
        "running": monitor.running,
        "history_limit": monitor.history_limit
    }
    if not validate_with_yang(status_data, "network-monitor", "/monitor-config"):
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Los datos no cumplen con el modelo YANG"
        )
    return status_data

@app.post("/restconf/data/network-monitor:update", 
          response_model=UpdateResponse,
          tags=["network-monitor"])
def force_update():
    """Forzar una actualización inmediata de los datos"""
    monitor.update_network_data()
    return {"result": "Datos actualizados manualmente"}

@app.put("/restconf/data/network-monitor:config", 
         response_model=MonitorConfigModel,
         tags=["network-monitor"])
def update_config(config: MonitorConfigModel):
    """Actualizar la configuración del monitor"""
    monitor.polling_interval = config.polling_interval
    monitor.bandwidth_threshold = config.bandwidth_threshold
    monitor.error_threshold = config.error_threshold
    monitor.history_limit = config.history_limit or monitor.history_limit
    
    if config.running and not monitor.running:
        monitor.start_monitoring()
    elif not config.running and monitor.running:
        monitor.stop_monitoring()
    
    return get_monitor_status()

@app.get("/.well-known/host-meta", include_in_schema=False)
def get_host_meta():
    """Endpoint de descubrimiento RESTCONF"""
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

@app.get("/restconf/data", include_in_schema=False)
def get_root():
    """Root resource para RESTCONF"""
    return JSONResponse(
        content={
            "ietf-restconf:restconf": {
                "data": {},
                "operations": {},
                "yang-library-version": "2016-06-21"
            }
        }
    )

if __name__ == "__main__":
    if not os.path.exists(YANG_MODELS_DIR):
        os.makedirs(YANG_MODELS_DIR)
        print(f"Directorio {YANG_MODELS_DIR} creado.")
    
    uvicorn.run(app, host="127.0.0.1", port=8000)