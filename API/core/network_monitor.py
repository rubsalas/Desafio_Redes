import requests
import json
from typing import List, Dict, Optional
import time
from datetime import datetime
import matplotlib.pyplot as plt
from dataclasses import dataclass
from collections import defaultdict
import threading

# Desactivar advertencias de SSL
requests.packages.urllib3.disable_warnings()

# Configuración RESTCONF
BASE_URL = "https://10.10.20.85/dna/intent/api/v1/network-device"
HEADERS = {
    #"Accept": "application/yang-data+json",
    #"Content-Type": "application/yang-data+json",
    #"Authorization": "Basic ZGV2ZWxvcGVyOkMxc2NvMTIzNDU="
    "X-Auth-Token":"eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY3RpdmVSRCI6IjFlMGFmNWQyZWM0ZDQ2ZTIyZDBhYmRlM2E1Y2RkYWNlN2RlZDNlOWQiLCJhdWQiOiJDRE5BIiwiYXV0aFNvdXJjZSI6ImxlZ2FjeSIsImNsaWVudElkIjoiYWRtaW5pc3RyYXRvciIsImVtYWlsIjoiYWRtaW5pc3RyYXRvckBsb2NhbHVzZXIuY29tIiwiZXhwIjoxNzUwNDY5NDQzLCJpYXQiOjE3NTA0NjU4NDMsImlzcyI6ImRuYWMiLCJyZHMiOlsiMWUwYWY1ZDJlYzRkNDZlMjJkMGFiZGUzYTVjZGRhY2U3ZGVkM2U5ZCJdLCJyZXNvdXJjZUdyb3VwcyI6Ikg0c0lBQUFBQUFBQS80cXVWaW91U2c1S0xjNHZMVXBPOVV4UnNsTFNVdEpSS3Frc1NGV3lVaXJPTEVsVnFvMEZCQUFBLy8rY3ZYZktKUUFBQUE9PSIsInJvbGVzIjpbIlNVUEVSLUFETUlOIl0sInNlc3Npb25JZCI6IjM0ZWMzMzlmLWViM2QtNTZhMC05MTA3LTRmYTE1YmFhMGE4MSIsInN1YiI6IjY4MGFiZTNkYmI1YTZiMDA1NmYxOTNkZiIsInRlbmFudElkIjoiNjdiOTM1YzU5MTU1ZjUwMDEzNTE1ZDFjIiwidGVuYW50TmFtZSI6IlROVDAiLCJ1c2VybmFtZSI6ImFkbWluaXN0cmF0b3IifQ.RjKtKD7JIlFxO-EPQoNTU1C06dyfS1OBYUKkR0QgCmHW9BW2OU6jnQCt3Gt59f_F9XNMBERBibslD6gD4eqbRQ",
    "Content-Type":"application/json"
}

POLLING_INTERVAL = 60  # segundos
HISTORY_LIMIT = 1440

@dataclass
class Alert:
    type: str
    message: str
    severity: str
    timestamp: str
    device_id: Optional[str] = None

@dataclass
class DeviceInfo:
    hostname: str
    managementIpAddress: str
    macAddress: str
    softwareVersion: str
    reachabilityStatus: str
    upTime: str
    serialNumber: str
    platformId: str
    interfaceCount: str
    lastUpdated: str
    id: str
    description: str = ""
    role: str = ""
    vendor: str = "Cisco"
    type: str = ""
    family: str = ""
    series: str = ""
    softwareType: str = ""
    deviceSupportLevel: str = ""
    collectionStatus: str = ""
    bootDateTime: str = ""

    def __post_init__(self):
        # Convertir interfaceCount a entero si es posible
        try:
            self.interfaceCount = int(self.interfaceCount)
        except (ValueError, TypeError):
            self.interfaceCount = 0

@dataclass
class DeviceResponse:
    response: List[DeviceInfo]
    version: str

class NetworkMonitor:
    def __init__(self):
        self.alerts: List[Alert] = []
        self.running = False
        self.polling_interval = POLLING_INTERVAL
        self.history_limit = HISTORY_LIMIT
        self.devices: List[DeviceInfo] = []
        self.device_history = defaultdict(list)

    def start_monitoring(self):
        self.running = True
        monitor_thread = threading.Thread(target=self._monitoring_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        print(f"Monitor iniciado. Actualizando cada {self.polling_interval} segundos...")

    def stop_monitoring(self):
        self.running = False
        print("Monitor detenido")

    def _monitoring_loop(self):
        while self.running:
            start_time = time.time()
            self.fetch_devices()
            self.check_for_alerts()
            self.update_history()
            if len(self.device_history.get(list(self.device_history.keys())[0], [])) % 5 == 0:
                self.generate_reports()
            elapsed = time.time() - start_time
            time.sleep(max(0, self.polling_interval - elapsed))

    def check_for_alerts(self):
        new_alerts = []
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for device in self.devices:
            # Verificar estado de alcanzabilidad
            if device.reachabilityStatus.lower() != "reachable":
                new_alerts.append(Alert(
                    type="DEVICE_UNREACHABLE",
                    message=f"El dispositivo {device.hostname} ({device.managementIpAddress}) no es alcanzable",
                    severity="critical",
                    timestamp=current_time,
                    device_id=device.id
                ))
            
            # Verificar si el dispositivo está soportado
            if device.deviceSupportLevel.lower() != "supported":
                new_alerts.append(Alert(
                    type="UNSUPPORTED_DEVICE",
                    message=f"El dispositivo {device.hostname} no está soportado (Estado: {device.deviceSupportLevel})",
                    severity="warning",
                    timestamp=current_time,
                    device_id=device.id
                ))
            
            # Verificar estado de colección
            if device.collectionStatus.lower() != "managed":
                new_alerts.append(Alert(
                    type="COLLECTION_ISSUE",
                    message=f"Problema con la colección de datos del dispositivo {device.hostname} (Estado: {device.collectionStatus})",
                    severity="warning",
                    timestamp=current_time,
                    device_id=device.id
                ))
            
            # Verificar tiempo de actividad (uptime) muy bajo (posible reinicio reciente)
            if ":" in device.upTime:
                try:
                    hours, minutes, seconds = map(float, device.upTime.split(":"))
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                    if total_seconds < 300:  # Menos de 5 minutos de uptime
                        new_alerts.append(Alert(
                            type="RECENT_REBOOT",
                            message=f"El dispositivo {device.hostname} se reinició recientemente (Uptime: {device.upTime})",
                            severity="warning",
                            timestamp=current_time,
                            device_id=device.id
                        ))
                except ValueError:
                    pass
        
        self.alerts = new_alerts

    def update_history(self):
        timestamp = datetime.now().isoformat()
        for device in self.devices:
            self.device_history[device.id].append({
                "timestamp": timestamp,
                "reachability": device.reachabilityStatus,
                "uptime": device.upTime,
                "interface_count": device.interfaceCount,
                "software_version": device.softwareVersion
            })
            
            # Limitar el historial según HISTORY_LIMIT
            if len(self.device_history[device.id]) > self.history_limit:
                self.device_history[device.id].pop(0)

    def generate_reports(self):
        print("Generando reportes...")
        self.generate_devices_table()
        self.generate_reachability_report()
        self.generate_alerts_report()

    def generate_devices_table(self) -> List[Dict]:
        devices_table = []
        for device in self.devices:
            devices_table.append({
                "hostname": device.hostname,
                "management_ip": device.managementIpAddress,
                "platform": device.platformId,
                "software_version": device.softwareVersion,
                "reachability": device.reachabilityStatus,
                "uptime": device.upTime,
                "interfaces": device.interfaceCount,
                "serial_number": device.serialNumber,
                "last_updated": device.lastUpdated,
                "device_id": device.id
            })
        
        with open("devices_table.json", "w") as f:
            json.dump(devices_table, f, indent=2)
        return devices_table

    def generate_reachability_report(self):
        if not self.device_history:
            print("No hay datos históricos de alcanzabilidad")
            return
        
        plt.figure(figsize=(12, 6))
        
        # Preparar datos para el gráfico
        device_status = {}
        for device_id, history in self.device_history.items():
            device = next((d for d in self.devices if d.id == device_id), None)
            if device:
                timestamps = [entry["timestamp"] for entry in history]
                reachability = [1 if entry["reachability"].lower() == "reachable" else 0 for entry in history]
                device_status[device.hostname] = (timestamps, reachability)
        
        # Crear gráfico para cada dispositivo
        for hostname, (timestamps, reachability) in device_status.items():
            plt.plot(timestamps, reachability, label=hostname)
        
        plt.title("Estado de Alcanzabilidad de Dispositivos (Histórico)")
        plt.ylabel("Alcanzable (1) / No Alcanzable (0)")
        plt.xlabel("Tiempo")
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.savefig("reachability_history.png")
        plt.close()
        print("Reporte de alcanzabilidad generado: reachability_history.png")

    def generate_alerts_report(self):
        if not self.alerts:
            print("No hay alertas para reportar")
            return
        
        alerts_data = [{
            "timestamp": alert.timestamp,
            "severity": alert.severity,
            "message": alert.message,
            "device_id": alert.device_id or "N/A"
        } for alert in self.alerts]
        
        with open("alerts_report.json", "w") as f:
            json.dump(alerts_data, f, indent=2)
        print("Reporte de alertas generado: alerts_report.json")

    def fetch_devices(self) -> bool:
        try:
            response = requests.get(BASE_URL, headers=HEADERS, verify=False)
            if response.status_code == 200:
                data = response.json()
                self._parse_devices(data)
                return True
            print(f"Error al obtener dispositivos: {response.status_code}")
            return False
        except Exception as e:
            print(f"Error en fetch_devices: {str(e)}")
            return False

    def _parse_devices(self, data: Dict):
        try:
            self.devices = []
            for device_data in data.get("response", []):
                device_info = DeviceInfo(
                    hostname=device_data.get("hostname", ""),
                    managementIpAddress=device_data.get("managementIpAddress", ""),
                    macAddress=device_data.get("macAddress", ""),
                    softwareVersion=device_data.get("softwareVersion", ""),
                    reachabilityStatus=device_data.get("reachabilityStatus", ""),
                    upTime=device_data.get("upTime", ""),
                    serialNumber=device_data.get("serialNumber", ""),
                    platformId=device_data.get("platformId", ""),
                    interfaceCount=str(device_data.get("interfaceCount", "0")),
                    lastUpdated=device_data.get("lastUpdated", ""),
                    id=device_data.get("id", ""),
                    description=device_data.get("description", ""),
                    role=device_data.get("role", ""),
                    vendor=device_data.get("vendor", "Cisco"),
                    type=device_data.get("type", ""),
                    family=device_data.get("family", ""),
                    series=device_data.get("series", ""),
                    softwareType=device_data.get("softwareType", ""),
                    deviceSupportLevel=device_data.get("deviceSupportLevel", ""),
                    collectionStatus=device_data.get("collectionStatus", ""),
                    bootDateTime=device_data.get("bootDateTime", "")
                )
                self.devices.append(device_info)
        except Exception as e:
            print(f"Error parsing devices: {str(e)}")
            raise

def main():
    print("Iniciando Monitor de Dispositivos de Red")
    monitor = NetworkMonitor()
    try:
        monitor.start_monitoring()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo monitor...")
        monitor.stop_monitoring()
        print("Aplicación finalizada")

if __name__ == "__main__":
    main()
