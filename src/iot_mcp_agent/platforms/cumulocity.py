"""
iot_mcp_agent/platforms/cumulocity.py

Cumulocity IoT REST API adapter.

Maps the generic tool interface to Cumulocity's REST API so the MCP server
can work with a real Cumulocity tenant without the agent knowing anything
about the underlying HTTP calls.

Cumulocity API docs: https://cumulocity.com/api/core/
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class CumulocityAdapter:
    """
    Thin async wrapper around the Cumulocity REST API.

    Uses httpx for async HTTP. All methods return plain dicts
    that match the same shape the simulator returns, so the MCP
    server and agents are platform-agnostic.
    """

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self._auth = (username, password)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=self._auth,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0,
        )

    async def list_devices(
        self,
        group: str | None = None,
        device_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> dict:
        params: dict[str, Any] = {
            "fragmentType": "c8y_IsDevice",
            "pageSize": limit,
        }
        if device_type:
            params["type"] = device_type
        if status:
            params["availability"] = status

        resp = await self._get("/inventory/managedObjects", params=params)
        devices = [self._normalise_device(d) for d in resp.get("managedObjects", [])]

        if group:
            # Filter by group name — in production you'd look up the group ID first
            devices = [d for d in devices if d.get("group") == group]

        return {"total": resp.get("statistics", {}).get("totalResult", len(devices)), "devices": devices}

    async def get_device(self, device_id: str) -> dict:
        resp = await self._get(f"/inventory/managedObjects/{device_id}")
        return self._normalise_device(resp)

    async def get_measurements(
        self,
        device_id: str,
        measurement_type: str | None = None,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int = 100,
    ) -> dict:
        params: dict[str, Any] = {
            "source": device_id,
            "pageSize": limit,
            "revert": "true",  # newest first
        }
        if measurement_type:
            params["type"] = measurement_type
        if from_time:
            params["dateFrom"] = from_time
        if to_time:
            params["dateTo"] = to_time
        else:
            params["dateTo"] = datetime.utcnow().isoformat() + "Z"
        if not from_time:
            params["dateFrom"] = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"

        resp = await self._get("/measurement/measurements", params=params)
        measurements = []
        for m in resp.get("measurements", []):
            for frag_key, frag_val in m.items():
                if frag_key.startswith("c8y_") and isinstance(frag_val, dict):
                    for series_key, series_val in frag_val.items():
                        measurements.append({
                            "timestamp": m.get("time"),
                            "type": frag_key,
                            "series": series_key,
                            "value": series_val.get("value"),
                            "unit": series_val.get("unit"),
                        })

        return {"device_id": device_id, "measurements": measurements}

    async def get_alarms(
        self,
        device_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> dict:
        params: dict[str, Any] = {"pageSize": limit}
        if device_id:
            params["source"] = device_id
        if severity:
            params["severity"] = severity
        if status:
            params["status"] = status or "ACTIVE"

        resp = await self._get("/alarm/alarms", params=params)
        alarms = [
            {
                "id": a.get("id"),
                "device_id": a.get("source", {}).get("id"),
                "type": a.get("type"),
                "severity": a.get("severity"),
                "status": a.get("status"),
                "text": a.get("text"),
                "created_at": a.get("creationTime"),
            }
            for a in resp.get("alarms", [])
        ]
        return {"total": len(alarms), "alarms": alarms}

    async def create_alarm(
        self, device_id: str, type: str, severity: str, text: str
    ) -> dict:
        payload = {
            "source": {"id": device_id},
            "type": type,
            "severity": severity,
            "status": "ACTIVE",
            "text": text,
            "time": datetime.utcnow().isoformat() + "Z",
        }
        resp = await self._post("/alarm/alarms", json=payload)
        return {"success": True, "alarm_id": resp.get("id"), "alarm": resp}

    async def update_device_config(
        self, device_id: str, config_key: str, config_value: Any, reason: str
    ) -> dict:
        # Store config in managed object custom fragment
        payload = {config_key: config_value, "agent_update_reason": reason}
        resp = await self._put(f"/inventory/managedObjects/{device_id}", json=payload)
        return {
            "success": True,
            "device_id": device_id,
            "updated": {config_key: config_value},
            "reason": reason,
        }

    async def send_notification(
        self,
        channel: str,
        recipient: str,
        subject: str,
        message: str,
        priority: str = "normal",
    ) -> dict:
        # In a real integration you'd call your notification service here
        # (e.g. Cumulocity SmartREST, AWS SNS, SendGrid, Slack webhook)
        logger.info(
            "NOTIFICATION [%s] to %s | %s | %s | priority=%s",
            channel, recipient, subject, message[:80], priority,
        )
        return {"success": True, "channel": channel, "recipient": recipient}

    async def get_device_group_summary(self, group_name: str) -> dict:
        # Look up the group managed object, then aggregate child devices
        params = {"type": "c8y_DeviceGroup", "text": group_name, "pageSize": 5}
        resp = await self._get("/inventory/managedObjects", params=params)
        groups = resp.get("managedObjects", [])
        if not groups:
            return {"error": f"Group '{group_name}' not found"}

        group_id = groups[0]["id"]
        children_resp = await self._get(
            f"/inventory/managedObjects/{group_id}/childAssets", params={"pageSize": 200}
        )
        devices = children_resp.get("references", [])
        return {
            "group": group_name,
            "group_id": group_id,
            "total_devices": len(devices),
        }

    # ── HTTP helpers ─────────────────────────────────────────────────────────

    async def _get(self, path: str, params: dict | None = None) -> dict:
        r = await self._client.get(path, params=params)
        r.raise_for_status()
        return r.json()

    async def _post(self, path: str, json: dict) -> dict:
        r = await self._client.post(path, json=json)
        r.raise_for_status()
        return r.json()

    async def _put(self, path: str, json: dict) -> dict:
        r = await self._client.put(path, json=json)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _normalise_device(raw: dict) -> dict:
        avail = raw.get("c8y_Availability", {}).get("status", "UNKNOWN")
        return {
            "id": raw.get("id"),
            "name": raw.get("name"),
            "type": raw.get("type"),
            "status": avail,
            "last_message": raw.get("lastUpdated"),
            "group": None,  # Populated separately if needed
        }
