# core/monitor_cli.py
import os
import requests

class NetworkMonitorCLI:
    """
    Clase para interactuar con la API RESTCONF del Network Monitor.
    Proporciona métodos que devuelven directamente los datos JSON.
    """
    def __init__(self, base_url=None):
        self.base_url = base_url or os.environ.get(
            "RESTCONF_BASE_URL",
            "http://localhost:8000/restconf/data"
        )
        self.headers = {"Accept": "application/yang-data+json"}

    def fetch_all_devices(self):
        url = f"{self.base_url}/network-devices:devices"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def fetch_device(self, device_id):
        url = f"{self.base_url}/network-devices:devices/device={device_id}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def fetch_history(self, device_id):
        url = f"{self.base_url}/network-devices:device-history/device={device_id}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def fetch_alerts(self):
        url = f"{self.base_url}/network-alerts:alerts"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def fetch_status(self):
        url = f"{self.base_url}/network-monitor:status"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()