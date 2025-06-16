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
    "X-Auth-Token":"eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY3RpdmVSRCI6IjFlMGFmNWQyZWM0ZDQ2ZTIyZDBhYmRlM2E1Y2RkYWNlN2RlZDNlOWQiLCJhdWQiOiJDRE5BIiwiYXV0aFNvdXJjZSI6ImxlZ2FjeSIsImNsaWVudElkIjoiYWRtaW5pc3RyYXRvciIsImVtYWlsIjoiYWRtaW5pc3RyYXRvckBsb2NhbHVzZXIuY29tIiwiZXhwIjoxNzUwMTA1NjYyLCJpYXQiOjE3NTAxMDIwNjIsImlzcyI6ImRuYWMiLCJyZHMiOlsiMWUwYWY1ZDJlYzRkNDZlMjJkMGFiZGUzYTVjZGRhY2U3ZGVkM2U5ZCJdLCJyZXNvdXJjZUdyb3VwcyI6Ikg0c0lBQUFBQUFBQS80cXVWaW91U2c1S0xjNHZMVXBPOVV4UnNsTFNVdEpSS3Frc1NGV3lVaXJPTEVsVnFvMEZCQUFBLy8rY3ZYZktKUUFBQUE9PSIsInJvbGVzIjpbIlNVUEVSLUFETUlOIl0sInNlc3Npb25JZCI6ImI1NTM2N2Q2LTJlOGMtNTAyNS1iMmQ4LTQ5NGIzNTM3NzhkNCIsInN1YiI6IjY4MGFiZTNkYmI1YTZiMDA1NmYxOTNkZiIsInRlbmFudElkIjoiNjdiOTM1YzU5MTU1ZjUwMDEzNTE1ZDFjIiwidGVuYW50TmFtZSI6IlROVDAiLCJ1c2VybmFtZSI6ImFkbWluaXN0cmF0b3IifQ.NE1wQ2D4djG3J3ZItAlW_B7mFUoeS6rEn7QloowbFlhnKceGjDfc-OidJt2FL0bwg96oCA0vjFzLrp7TZBgNQA",
    "Content-Type":"application/json"
}

POLLING_INTERVAL = 60  # segundos
HISTORY_LIMIT = 1440

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
    interfaceCount: str  # Cambiado a str para coincidir con el JSON
    lastUpdated: str
    id: str = None  # Hacer opcional y asignar después
    description: str = ""
    role: str = ""
    vendor: str = "Cisco"
    type: str = ""
    family: str = ""
    series: str = ""

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
        self.interfaces: List[Interface] = []
        self.alerts: List[Alert] = []
        self.bandwidth_history = defaultdict(list)
        self.error_history = defaultdict(list)
        self.running = False
        self.polling_interval = POLLING_INTERVAL
        self.history_limit = HISTORY_LIMIT
        self.bandwidth_threshold = 70
        self.error_threshold = 5
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
            #self.update_network_data()
            self.fetch_devices()
            elapsed = time.time() - start_time
            time.sleep(max(0, self.polling_interval - elapsed))

    def update_network_data(self):
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Actualizando datos...")
        if self.fetch_interfaces():
            for interface in self.interfaces:
                self.fetch_interface_stats(interface.name)
            self.check_for_alerts()
            self.update_history()
            if len(self.bandwidth_history.get(list(self.bandwidth_history.keys())[0], [])) % 5 == 0:
                self.generate_reports()
        else:
            print("Error al actualizar datos de red")

    def fetch_interfaces(self) -> bool:
        try:
            url = f"{BASE_URL}/ietf-interfaces:interfaces"
            response = requests.get(url, headers=HEADERS, verify=False)
            if response.status_code == 200:
                data = response.json()
                self._parse_interfaces(data)
                return True
            else:
                print(f"Error al obtener interfaces: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error en fetch_interfaces: {str(e)}")
            return False

    def _parse_interfaces(self, data: Dict):
        new_interfaces = []
        for iface_data in data.get("ietf-interfaces:interfaces", {}).get("interface", []):
            ipv4 = None
            ipv6 = None
            ipv4_data = iface_data.get("ietf-ip:ipv4", {}).get("address", [{}])[0]
            if ipv4_data.get("ip"):
                ipv4 = InterfaceIP(ip=ipv4_data.get("ip"), netmask=ipv4_data.get("netmask", ""))
            ipv6_data = iface_data.get("ietf-ip:ipv6", {}).get("address", [{}])[0]
            if ipv6_data.get("ip"):
                ipv6 = InterfaceIP(ip=ipv6_data.get("ip"), netmask=ipv6_data.get("prefix-length", ""))
            interface = Interface(
                name=iface_data.get("name", ""),
                description=iface_data.get("description", ""),
                enabled=iface_data.get("enabled", False),
                oper_status=iface_data.get("oper-status", "unknown"),
                ipv4=ipv4,
                ipv6=ipv6,
                speed=iface_data.get("speed", None)
            )
            new_interfaces.append(interface)
        self.interfaces = new_interfaces

    def fetch_interface_stats(self, interface_name: str) -> bool:
        try:
            url = f"{BASE_URL}/ietf-interfaces:interfaces-state/interface={interface_name}"
            response = requests.get(url, headers=HEADERS, verify=False)
            if response.status_code == 200:
                data = response.json()
                self._parse_interface_stats(interface_name, data)
                return True
            else:
                print(f"Error al obtener stats para {interface_name}: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error en fetch_interface_stats: {str(e)}")
            return False

    def _parse_interface_stats(self, interface_name: str, data: Dict):
        stats_data = data.get("ietf-interfaces:interface", {})
        if "statistics" in stats_data:
            stats = InterfaceStats(
                in_octets=int(stats_data["statistics"].get("in-octets", 0)),
                out_octets=int(stats_data["statistics"].get("out-octets", 0)),
                in_errors=int(stats_data["statistics"].get("in-errors", 0)),
                out_errors=int(stats_data["statistics"].get("out-errors", 0)),
                last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            for interface in self.interfaces:
                if interface.name == interface_name:
                    interface.stats = stats
                    break

    def check_for_alerts(self):
        new_alerts = []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for interface in self.interfaces:
            if not interface.enabled or interface.oper_status.lower() != "up":
                new_alerts.append(Alert(
                    type="INTERFACE_DOWN",
                    message=f"La interfaz {interface.name} está {'deshabilitada' if not interface.enabled else 'operacionalmente caída'}",
                    severity="critical",
                    timestamp=current_time,
                    interface=interface.name
                ))
            if not interface.ipv4 and not interface.ipv6:
                new_alerts.append(Alert(
                    type="NO_IP_ASSIGNED",
                    message=f"La interfaz {interface.name} no tiene dirección IP asignada",
                    severity="warning",
                    timestamp=current_time,
                    interface=interface.name
                ))
            if interface.stats and (interface.stats.in_errors > self.error_threshold or interface.stats.out_errors > self.error_threshold):
                new_alerts.append(Alert(
                    type="HIGH_ERROR_RATE",
                    message=f"La interfaz {interface.name} tiene {interface.stats.in_errors} errores de entrada y {interface.stats.out_errors} de salida",
                    severity="warning",
                    timestamp=current_time,
                    interface=interface.name
                ))
        self.alerts = new_alerts

    def update_history(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for interface in self.interfaces:
            if interface.stats:
                max_bandwidth = interface.speed * 1e6 if interface.speed else 1e9
                bandwidth_usage = ((interface.stats.in_octets + interface.stats.out_octets) * 8 / max_bandwidth) * 100
                self.bandwidth_history[interface.name].append((current_time, bandwidth_usage))
                self.error_history[interface.name].append((current_time, interface.stats.in_errors + interface.stats.out_errors))
                if len(self.bandwidth_history[interface.name]) > self.history_limit:
                    self.bandwidth_history[interface.name].pop(0)
                    self.error_history[interface.name].pop(0)

    def generate_reports(self):
        print("Generando reportes...")
        self.generate_interfaces_table()
        self.generate_bandwidth_report()
        self.generate_alerts_report()

    def generate_interfaces_table(self) -> List[Dict]:
        interfaces_table = []
        for iface in self.interfaces:
            ip_info = ""
            if iface.ipv4:
                ip_info = f"IPv4: {iface.ipv4.ip}/{iface.ipv4.netmask}"
            if iface.ipv6:
                ip_info += f", IPv6: {iface.ipv6.ip}/{iface.ipv6.netmask}" if ip_info else f"IPv6: {iface.ipv6.ip}/{iface.ipv6.netmask}"
            interfaces_table.append({
                "name": iface.name,
                "description": iface.description,
                "status": "UP" if iface.enabled and iface.oper_status.lower() == "up" else "DOWN",
                "enabled": "Sí" if iface.enabled else "No",
                "ip_info": ip_info if ip_info else "N/A",
                "speed": f"{iface.speed} Mbps" if iface.speed else "Desconocido"
            })
        with open("interfaces_table.json", "w") as f:
            json.dump(interfaces_table, f, indent=2)
        return interfaces_table

    def generate_bandwidth_report(self):
        if not self.bandwidth_history:
            print("No hay datos históricos de ancho de banda")
            return
        plt.figure(figsize=(12, 6))
        for interface, data in self.bandwidth_history.items():
            timestamps = [d[0] for d in data]
            values = [d[1] for d in data]
            plt.plot(timestamps, values, label=interface)
        plt.title("Uso de Ancho de Banda por Interfaz (Histórico)")
        plt.ylabel("Porcentaje de Uso")
        plt.xlabel("Tiempo")
        plt.xticks(rotation=45)
        plt.axhline(y=self.bandwidth_threshold, color='r', linestyle='--', label='Umbral de Alerta')
        plt.legend()
        plt.tight_layout()
        plt.savefig("bandwidth_history.png")
        plt.close()
        print("Reporte de ancho de banda generado: bandwidth_history.png")

    def generate_alerts_report(self):
        if not self.alerts:
            print("No hay alertas para reportar")
            return
        alerts_data = [{
            "timestamp": alert.timestamp,
            "severity": alert.severity,
            "message": alert.message,
            "interface": alert.interface or "N/A"
        } for alert in self.alerts]
        with open("alerts_report.json", "w") as f:
            json.dump(alerts_data, f, indent=2)
        print("Reporte de alertas generado: alerts_report.json")

    def fetch_devices(self) -> bool:
        try:
            url = f"{BASE_URL}/"
            response = requests.get(url, headers=HEADERS, verify=False)
            if response.status_code == 200:
                data = response.json()
                self._parse_devices(data)
                return True
            print("Error:" + str(response.status_code))
            return False
        except Exception as e:
            print(f"Error fetching devices: {str(e)}")
            return False

    def _parse_devices(self, data: Dict):
        try:
            self.devices = []
            for device_data in data.get("response", []):
                # Asignar el ID basado en instanceUuid si existe
                device_id = device_data.get("instanceUuid") or device_data.get("id")
                device_info = DeviceInfo(
                    id=device_id,
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
                    description=device_data.get("description", ""),
                    role=device_data.get("role", ""),
                    vendor=device_data.get("vendor", "Cisco"),
                    type=device_data.get("type", ""),
                    family=device_data.get("family", ""),
                    series=device_data.get("series", "")
                )
                self.devices.append(device_info)
            
            self._update_device_history()
        except Exception as e:
            print(f"Error parsing devices: {str(e)}")
            raise

    def _update_device_history(self):
        timestamp = datetime.now().isoformat()
        for device in self.devices:
            print("Dispotivo: " + device.id + ". Estado: " + device.reachabilityStatus)
            self.device_history[device.id].append({
                "timestamp": timestamp,
                "reachability": device.reachabilityStatus,
                "uptime": device.upTime,
                "interface_count": device.interfaceCount
            })

def main():
    print("Iniciando Monitor de Red con RESTCONF")
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
