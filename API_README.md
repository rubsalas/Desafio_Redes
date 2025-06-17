# Network Monitor RESTCONF API Endpoints

## Base URL: <http://localhost:8000/restconf/data>

## DEVICE ENDPOINTS

### 1. Get all devices

`GET /network-monitor:devices`
Headers:
  `Accept: application/yang-data+json`

Example Response:

```json
[
    {
        "id": "bfea531c-f8ff-476f-91c7-def7953b7706",
        "hostname": "sw1",
        "macAddress": "52:54:00:02:19:54",
        "managementIpAddress": "10.10.20.175",
        "softwareVersion": "17.12.1prd9",
        "reachabilityStatus": "Reachable",
        "upTime": "0:10:03.00",
        "serialNumber": "CML12345UAD",
        "platformId": "C9KV-UADP-8P",
        "interfaceCount": 8,
        "lastUpdated": "2025-06-16 00:29:04"
    }
]
```

### 2. Get single device

`GET /network-monitor:devices/device={device_id}`
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
  "upTime": "0:10:03.00",
  "serialNumber": "CML12345UAD",
  "platformId": "C9KV-UADP-8P",
  "interfaceCount": 8,
  "lastUpdated": "2025-06-16 00:29:04"
}
```

### 3. Get device history

`GET /network-monitor:device-history/device={device_id}`
Params:
  `device_id: string (UUID)`

Example Response:

```json
[
  {
    "timestamp": "2025-06-16T00:29:04",
    "reachability": "Reachable",
    "uptime": 12557,
    "interface_count": 8
  }
]
```

## INTERFACE ENDPOINTS

### 4. Get all interfaces

`GET /network-monitor:interfaces`
Headers:
  `Accept: application/yang-data+json`

Example Response:

```json
[
  {
    "name": "GigabitEthernet1",
    "description": "Uplink to core",
    "enabled": true,
    "oper_status": "up",
    "ipv4": {
      "ip": "192.168.1.1",
      "netmask": "255.255.255.0"
    },
    "speed": 1000,
    "stats": {
      "in_octets": 125689745,
      "out_octets": 98756321,
      "in_errors": 2,
      "out_errors": 0,
      "last_updated": "2025-06-16T14:30:45"
    }
  }
]
```

### 5. Get single interface

`GET /network-monitor:interfaces/interface={interface_name}`
Params:
  `interface_name: string`

Example Response:

```json
{
  "name": "GigabitEthernet1",
  "description": "Uplink to core",
  "enabled": true,
  "oper_status": "up",
  "ipv4": {
    "ip": "192.168.1.1",
    "netmask": "255.255.255.0"
  },
  "speed": 1000
}
```

## ALERT ENDPOINTS

### 6. Get all alerts

`GET /network-monitor:alerts`

Example Response:

```json
[
  {
    "type": "INTERFACE_DOWN",
    "message": "Interface GigabitEthernet2 is down",
    "severity": "critical",
    "timestamp": "2025-06-16T14:31:22",
    "interface": "GigabitEthernet2"
  }
]
```

## HISTORY ENDPOINTS

### 7. Get bandwidth history

`GET /network-monitor:bandwidth-history`

Example Response:

```json
{
  "GigabitEthernet1": [
    {
      "timestamp": "2025-06-16T14:30:00",
      "value": 45.2
    }
  ]
}
```

### 8. Get error history

`GET /network-monitor:error-history`

Example Response:

```json
{
  "GigabitEthernet1": [
    {
      "timestamp": "2025-06-16T14:30:00",
      "value": 2
    }
  ]
}
```

## CONTROL ENDPOINTS

### 9. Force data update

`POST /network-monitor:update`

Example Response:

```json
{
  "result": "Data update initiated"
}
```

### 10. Update monitor config

`PUT /network-monitor:config`
Body:

```json
{
  "polling_interval": 30,
  "bandwidth_threshold": 80.0,
  "error_threshold": 10
}
```

Example Response:

```json
{
  "polling_interval": 30,
  "bandwidth_threshold": 80.0,
  "error_threshold": 10,
  "running": true
}
```

## STATUS ENDPOINTS

### 11. Get monitor status

`GET /network-monitor:status`

Example Response:

```json
{
  "polling_interval": 30,
  "bandwidth_threshold": 80.0,
  "error_threshold": 10,
  "running": true,
  "history_limit": 1440
}
```
