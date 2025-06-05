import requests
import json
from typing import List, Dict, Optional, Tuple
import time
from datetime import datetime
import matplotlib.pyplot as plt
from dataclasses import dataclass
from collections import defaultdict
import threading

# Desactivar advertencias de SSL (solo para desarrollo)
requests.packages.urllib3.disable_warnings()

# Configuración básica
BASE_URL = "https://sandbox-iosxe-latest-1.cisco.com/restconf/data"
HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
    "Authorization": "Basic ZGV2ZWxvcGVyOkMxc2NvMTIzNDU="  # Credenciales públicas de Cisco Sandbox
}

# Constantes de configuración
POLLING_INTERVAL = 60  # Segundos entre actualizaciones
HISTORY_LIMIT = 1440    # Límite de puntos históricos (24h con intervalos de 1 min)

# Modelo de datos para interfaces de red
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
    speed: Optional[int] = None  # en Mbps
    stats: Optional[InterfaceStats] = None

@dataclass
class Alert:
    type: str
    message: str
    severity: str  # critical, warning, info
    timestamp: str
    interface: Optional[str] = None

class NetworkMonitor:
    def __init__(self):
        self.interfaces: List[Interface] = []
        self.alerts: List[Alert] = []
        self.bandwidth_history = defaultdict(list)  # Historial de ancho de banda por interfaz
        self.error_history = defaultdict(list)     # Historial de errores por interfaz
        self.running = False
        self.polling_interval = POLLING_INTERVAL
        self.history_limit = HISTORY_LIMIT
        
        # Umbrales para alertas
        self.bandwidth_threshold = 70  # % para alertas de ancho de banda
        self.error_threshold = 5       # Número de errores para alerta

    def start_monitoring(self):
        """Inicia el monitoreo continuo en un hilo separado"""
        self.running = True
        monitor_thread = threading.Thread(target=self._monitoring_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        print(f"Monitor iniciado. Actualizando cada {self.polling_interval} segundos...")

    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.running = False
        print("Monitor detenido")

    def _monitoring_loop(self):
        """Bucle principal de monitoreo"""
        while self.running:
            start_time = time.time()
            
            # Actualizar datos
            self.update_network_data()
            
            # Calcular tiempo restante hasta la próxima actualización
            elapsed = time.time() - start_time
            sleep_time = max(0, self.polling_interval - elapsed)
            time.sleep(sleep_time)

    def update_network_data(self):
        """Actualiza todos los datos de red"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Actualizando datos...")
        
        # Paso 1: Obtener datos de interfaces
        if self.fetch_interfaces():
            # Paso 2: Obtener estadísticas para cada interfaz
            for interface in self.interfaces:
                self.fetch_interface_stats(interface.name)
            
            # Paso 3: Verificar alertas
            self.check_for_alerts()
            
            # Paso 4: Actualizar historiales
            self.update_history()
            
            # Paso 5: Generar reportes (cada 5 actualizaciones)
            if len(self.bandwidth_history.get(list(self.bandwidth_history.keys())[0] if self.bandwidth_history else [], [])) % 5 == 0:
                self.generate_reports()
        else:
            print("Error al actualizar datos de red")

    def fetch_interfaces(self) -> bool:
        """Obtiene datos de interfaces via RESTCONF"""
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
        """Parsea los datos de interfaces del JSON recibido"""
        new_interfaces = []
        
        for iface_data in data.get("ietf-interfaces:interfaces", {}).get("interface", []):
            ipv4 = None
            ipv6 = None
            
            # Manejar IPv4
            ipv4_data = iface_data.get("ietf-ip:ipv4", {}).get("address", [{}])[0]
            if ipv4_data.get("ip"):
                ipv4 = InterfaceIP(ip=ipv4_data.get("ip"), netmask=ipv4_data.get("netmask", ""))
            
            # Manejar IPv6 (ejemplo)
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
        """Obtiene estadísticas de una interfaz específica"""
        try:
            url = f"{BASE_URL}/interfaces-state/interface={interface_name}"
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
        """Parsea las estadísticas de una interfaz"""
        stats_data = data.get("ietf-interfaces:interface", {})
        
        if "statistics" in stats_data:
            stats = InterfaceStats(
                in_octets=int(stats_data["statistics"].get("in-octets", 0)),
                out_octets=int(stats_data["statistics"].get("out-octets", 0)),
                in_errors=int(stats_data["statistics"].get("in-errors", 0)),
                out_errors=int(stats_data["statistics"].get("out-errors", 0)),
                last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Actualizar la interfaz correspondiente
            for interface in self.interfaces:
                if interface.name == interface_name:
                    interface.stats = stats
                    break

    def check_for_alerts(self):
        """Verifica condiciones que generan alertas"""
        new_alerts = []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for interface in self.interfaces:
            # Alerta 1: Interfaz caída (enabled: false o oper-status: down)
            if not interface.enabled or interface.oper_status.lower() != "up":
                new_alerts.append(Alert(
                    type="INTERFACE_DOWN",
                    message=f"La interfaz {interface.name} está {'deshabilitada' if not interface.enabled else 'operacionalmente caída'}",
                    severity="critical",
                    timestamp=current_time,
                    interface=interface.name
                ))
            
            # Alerta 2: Sin dirección IP asignada
            if not interface.ipv4 and not interface.ipv6:
                new_alerts.append(Alert(
                    type="NO_IP_ASSIGNED",
                    message=f"La interfaz {interface.name} no tiene dirección IP asignada",
                    severity="warning",
                    timestamp=current_time,
                    interface=interface.name
                ))
            
            # Alerta 3: Errores en la interfaz
            if interface.stats and (interface.stats.in_errors > self.error_threshold or 
                                   interface.stats.out_errors > self.error_threshold):
                new_alerts.append(Alert(
                    type="HIGH_ERROR_RATE",
                    message=f"La interfaz {interface.name} tiene {interface.stats.in_errors} errores de entrada y {interface.stats.out_errors} de salida",
                    severity="warning",
                    timestamp=current_time,
                    interface=interface.name
                ))
        
        # Solo mantener las alertas no resueltas (simplificado)
        self.alerts = new_alerts

    def update_history(self):
        """Actualiza los historiales de métricas"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for interface in self.interfaces:
            if interface.stats:
                # Calcular uso de ancho de banda (simulado como % del máximo teórico)
                max_bandwidth = interface.speed * 1e6 if interface.speed else 1e9  # 1 Gbps por defecto
                bandwidth_usage = ((interface.stats.in_octets + interface.stats.out_octets) * 8 / max_bandwidth) * 100
                
                # Agregar al historial
                self.bandwidth_history[interface.name].append((current_time, bandwidth_usage))
                self.error_history[interface.name].append((current_time, interface.stats.in_errors + interface.stats.out_errors))
                
                # Limitar el tamaño del historial
                if len(self.bandwidth_history[interface.name]) > self.history_limit:
                    self.bandwidth_history[interface.name].pop(0)
                    self.error_history[interface.name].pop(0)

    def generate_reports(self):
        """Genera todos los reportes necesarios"""
        print("Generando reportes...")
        self.generate_interfaces_table()
        self.generate_bandwidth_report()
        self.generate_alerts_report()

    def generate_interfaces_table(self) -> List[Dict]:
        """Genera y devuelve una tabla con la información de las interfaces"""
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
        
        # Guardar como JSON para la interfaz
        with open("interfaces_table.json", "w") as f:
            json.dump(interfaces_table, f, indent=2)
            
        return interfaces_table

    def generate_bandwidth_report(self):
        """Genera gráficos de uso de ancho de banda"""
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
        """Genera un reporte de alertas"""
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

def main():
    print("Iniciando Monitor de Red con RESTCONF - Versión Mejorada")
    monitor = NetworkMonitor()
    
    try:
        # Iniciar monitoreo continuo
        monitor.start_monitoring()
        
        # Mantener el programa en ejecución
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nDeteniendo monitor...")
        monitor.stop_monitoring()
        print("Aplicación finalizada")

if __name__ == "__main__":
    main()