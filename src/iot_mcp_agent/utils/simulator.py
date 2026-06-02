"""
iot_mcp_agent/utils/simulator.py

Realistic IoT device simulator.

Generates synthetic telemetry, devices, alarms, and groups so the full
agentic loop can be tested and demonstrated without real hardware or
a live IoT platform subscription.
"""

import math
import random
import uuid
from datetime import datetime, timedelta
from typing import Any


class DeviceSimulator:
    """
    Simulates a fleet of industrial IoT devices.

    Generates:
    - Factory floor temperature sensors with realistic daily cycles
    - Motor vibration sensors with simulated degradation
    - Environmental sensors (humidity, CO2)
    - Device groups and hierarchies
    - Pre-seeded anomalies for the agent to discover
    """

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)
        self._devices = self._generate_devices()
        self._alarm_store: list[dict] = []
        self._config_store: dict[str, dict] = {}

    # ── Public adapter interface ─────────────────────────────────────────────

    async def list_devices(
        self,
        group: str | None = None,
        device_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> dict:
        devices = list(self._devices.values())
        if group:
            devices = [d for d in devices if d["group"] == group]
        if device_type:
            devices = [d for d in devices if d["type"] == device_type]
        if status:
            devices = [d for d in devices if d["status"] == status]
        return {
            "total": len(devices),
            "devices": devices[:limit],
        }

    async def get_device(self, device_id: str) -> dict:
        device = self._devices.get(device_id)
        if not device:
            return {"error": f"Device {device_id} not found"}
        cfg = self._config_store.get(device_id, {})
        return {**device, "config": cfg}

    async def get_measurements(
        self,
        device_id: str,
        measurement_type: str | None = None,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int = 100,
    ) -> dict:
        device = self._devices.get(device_id)
        if not device:
            return {"error": f"Device {device_id} not found"}

        # Generate extra readings to ensure coverage of the requested time range
        readings = self._generate_readings(device, limit * 3)
        if measurement_type:
            readings = [r for r in readings if r["type"] == measurement_type]

        # Filter by time range if from_time or to_time is specified
        if from_time or to_time:
            try:
                # Parse ISO format timestamps, handling both with and without 'Z' suffix
                from_dt = (
                    datetime.fromisoformat(from_time.replace("Z", "+00:00")) if from_time else None
                )
                to_dt = datetime.fromisoformat(to_time.replace("Z", "+00:00")) if to_time else None

                readings = [
                    r
                    for r in readings
                    if (
                        from_dt is None
                        or datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) >= from_dt
                    )
                    and (
                        to_dt is None
                        or datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) <= to_dt
                    )
                ]
            except (ValueError, AttributeError):
                # If time parsing fails, return all readings as-is
                pass

        return {
            "device_id": device_id,
            "device_name": device["name"],
            "measurements": readings[:limit],
            "unit": readings[0]["unit"] if readings else None,
        }

    async def get_alarms(
        self,
        device_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> dict:
        alarms = list(self._alarm_store)
        if device_id:
            alarms = [a for a in alarms if a["device_id"] == device_id]
        if severity:
            alarms = [a for a in alarms if a["severity"] == severity]
        if status:
            alarms = [a for a in alarms if a["status"] == status]
        return {"total": len(alarms), "alarms": alarms[:limit]}

    async def create_alarm(self, device_id: str, type: str, severity: str, text: str) -> dict:
        alarm = {
            "id": str(uuid.uuid4())[:8],
            "device_id": device_id,
            "device_name": self._devices.get(device_id, {}).get("name", "Unknown"),
            "type": type,
            "severity": severity,
            "status": "ACTIVE",
            "text": text,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._alarm_store.append(alarm)
        return {"success": True, "alarm_id": alarm["id"], "alarm": alarm}

    async def update_device_config(
        self, device_id: str, config_key: str, config_value: Any, reason: str
    ) -> dict:
        if device_id not in self._devices:
            return {"error": f"Device {device_id} not found"}
        if device_id not in self._config_store:
            self._config_store[device_id] = {}
        self._config_store[device_id][config_key] = config_value
        return {
            "success": True,
            "device_id": device_id,
            "updated": {config_key: config_value},
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def send_notification(
        self,
        channel: str,
        recipient: str,
        subject: str,
        message: str,
        priority: str = "normal",
    ) -> dict:
        # In simulator, just acknowledge the notification
        return {
            "success": True,
            "channel": channel,
            "recipient": recipient,
            "subject": subject,
            "priority": priority,
            "sent_at": datetime.utcnow().isoformat(),
            "note": "[SIMULATED — no actual notification sent]",
        }

    async def get_device_group_summary(self, group_name: str) -> dict:
        devices = [d for d in self._devices.values() if d["group"] == group_name]
        if not devices:
            return {"error": f"Group '{group_name}' not found or empty"}

        online = sum(1 for d in devices if d["status"] == "AVAILABLE")
        offline = sum(1 for d in devices if d["status"] == "UNAVAILABLE")
        active_alarms = [a for a in self._alarm_store if a["status"] == "ACTIVE"]
        group_alarms = [a for a in active_alarms if a["device_id"] in {d["id"] for d in devices}]
        return {
            "group": group_name,
            "total_devices": len(devices),
            "online": online,
            "offline": offline,
            "maintenance": len(devices) - online - offline,
            "active_alarms": len(group_alarms),
            "critical_alarms": sum(1 for a in group_alarms if a["severity"] == "CRITICAL"),
            "device_types": list({d["type"] for d in devices}),
        }

    # ── Private generators ───────────────────────────────────────────────────

    def _generate_devices(self) -> dict[str, dict]:
        devices = {}

        specs = [
            # (name_prefix, count, type, group, normally_available)
            ("TempSensor", 8, "c8y_TemperatureSensor", "Factory Floor", True),
            ("Motor", 5, "c8y_VibrationSensor", "Pump Station", True),
            ("EnvSensor", 4, "c8y_EnvironmentalSensor", "Warehouse", True),
            ("Gateway", 2, "c8y_Gateway", "Network", True),
        ]

        for prefix, count, dtype, group, avail in specs:
            for i in range(1, count + 1):
                did = f"{prefix.lower()}-{i:03d}"
                # Simulate some devices offline
                status = "AVAILABLE"
                if not avail or (prefix == "Motor" and i == 3):
                    status = "UNAVAILABLE"
                devices[did] = {
                    "id": did,
                    "name": f"{prefix}-{i:03d}",
                    "type": dtype,
                    "group": group,
                    "status": status,
                    "last_message": (
                        datetime.utcnow() - timedelta(seconds=self._rng.randint(10, 300))
                    ).isoformat(),
                    "firmware": "v2.4.1",
                    "signal_strength": self._rng.randint(60, 100) if status == "AVAILABLE" else 0,
                }

        return devices

    def _generate_readings(self, device: dict, count: int) -> list[dict]:
        dtype = device["type"]
        now = datetime.utcnow()

        if dtype == "c8y_TemperatureSensor":
            return self._temperature_readings(device, count, now)
        elif dtype == "c8y_VibrationSensor":
            return self._vibration_readings(device, count, now)
        elif dtype == "c8y_EnvironmentalSensor":
            return self._env_readings(device, count, now)
        return []

    def _temperature_readings(self, device: dict, count: int, now: datetime) -> list[dict]:
        """Realistic temperature with daily cycle + injected anomaly on sensor-005."""
        readings = []
        is_faulty = device["id"] == "tempsensor-005"
        for i in range(count):
            t = now - timedelta(minutes=i * 5)
            hour = t.hour + t.minute / 60
            # Normal daily cycle: 18–28°C
            base = 23 + 5 * math.sin((hour - 6) * math.pi / 12)
            noise = self._rng.gauss(0, 0.3)
            # Inject a spike on the faulty sensor
            spike = 65 if is_faulty and i < 6 else 0
            value = round(base + noise + spike, 1)
            readings.append(
                {
                    "timestamp": t.isoformat(),
                    "type": "c8y_Temperature",
                    "value": value,
                    "unit": "°C",
                }
            )
        return readings

    def _vibration_readings(self, device: dict, count: int, now: datetime) -> list[dict]:
        """Vibration with a gradual degradation trend on motor-002."""
        readings = []
        is_degrading = device["id"] == "motor-002"
        for i in range(count):
            t = now - timedelta(minutes=i * 10)
            base = 1.2
            noise = self._rng.gauss(0, 0.08)
            trend = (count - i) * 0.03 if is_degrading else 0
            value = round(base + noise + trend, 3)
            readings.append(
                {
                    "timestamp": t.isoformat(),
                    "type": "c8y_Vibration",
                    "value": value,
                    "unit": "mm/s",
                }
            )
        return readings

    def _env_readings(self, device: dict, count: int, now: datetime) -> list[dict]:
        readings = []
        for i in range(count):
            t = now - timedelta(minutes=i * 15)
            readings.append(
                {
                    "timestamp": t.isoformat(),
                    "type": "c8y_Humidity",
                    "value": round(self._rng.uniform(40, 70), 1),
                    "unit": "%RH",
                }
            )
        return readings
