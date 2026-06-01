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

    Uses httpx for async HTTP. All methods return plain dicts with the exact
    same schema as the simulator, ensuring platform-agnostic agent behavior
    regardless of whether using 'simulate' or 'cumulocity' backend.

    Usage:
        async with CumulocityAdapter(base_url, user, pwd) as adapter:
            devices = await adapter.list_devices()

    Or for long-lived adapters, explicitly call aclose():
        adapter = CumulocityAdapter(base_url, user, pwd)
        try:
            devices = await adapter.list_devices()
        finally:
            await adapter.aclose()
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

    async def aclose(self) -> None:
        """Close the underlying httpx AsyncClient to clean up resources."""
        await self._client.aclose()

    async def __aenter__(self) -> "CumulocityAdapter":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit — closes the client."""
        await self.aclose()

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
            # Filter by group name. Note: Cumulocity stores group membership via child asset
            # relationships on the group managed object, not on individual devices. This filters
            # by a custom group field if present; for full group membership queries, use
            # get_device_group_summary() or look up the group ID and query its child assets.
            devices = [d for d in devices if d.get("group") == group]

        return {
            "total": resp.get("statistics", {}).get("totalResult", len(devices)),
            "devices": devices,
        }

    async def get_device(self, device_id: str) -> dict:
        resp = await self._get(f"/inventory/managedObjects/{device_id}")
        device = self._normalise_device(resp)
        # Extract custom config fragments from the response
        # (any custom fragments beyond standard c8y_* fields)
        config = {}
        for key, val in resp.items():
            if not key.startswith("c8y_") and key not in ("id", "name", "type", "lastUpdated"):
                config[key] = val
        device["config"] = config
        return device

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
                        measurements.append(
                            {
                                "timestamp": m.get("time"),
                                "type": frag_key,
                                "series": series_key,
                                "value": series_val.get("value"),
                                "unit": series_val.get("unit"),
                            }
                        )

        # Get device name for consistency with simulator response shape
        device_name = "Unknown"
        try:
            device_resp = await self._get(f"/inventory/managedObjects/{device_id}")
            device_name = device_resp.get("name", device_id)
        except Exception:
            # If lookup fails, fall back to device_id
            device_name = device_id

        # Extract unit from first measurement if available
        unit = measurements[0]["unit"] if measurements else None

        return {
            "device_id": device_id,
            "device_name": device_name,
            "measurements": measurements[:limit],
            "unit": unit,
        }

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

    async def create_alarm(self, device_id: str, type: str, severity: str, text: str) -> dict:
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
            channel,
            recipient,
            subject,
            message[:80],
            priority,
        )
        return {"success": True, "channel": channel, "recipient": recipient}

    async def get_device_group_summary(self, group_name: str) -> dict:
        """
        Get aggregated health summary for all devices in a group.

        Fetches the group, retrieves all child devices, and aggregates their
        status, alarms, and types to match the simulator response schema.
        """
        # Look up the group managed object
        params = {"type": "c8y_DeviceGroup", "text": group_name, "pageSize": 5}
        resp = await self._get("/inventory/managedObjects", params=params)
        groups = resp.get("managedObjects", [])
        if not groups:
            return {"error": f"Group '{group_name}' not found"}

        group_id = groups[0]["id"]
        children_resp = await self._get(
            f"/inventory/managedObjects/{group_id}/childAssets", params={"pageSize": 200}
        )
        child_refs = children_resp.get("references", [])

        # Fetch full device objects to get status
        devices = []
        for ref in child_refs:
            try:
                device_id = ref.get("id")
                if device_id:
                    device = await self._get(f"/inventory/managedObjects/{device_id}")
                    devices.append(device)
            except Exception as exc:
                logger.debug("Failed to fetch device %s: %s", ref.get("id"), exc)

        # Aggregate device status
        online = sum(
            1 for d in devices if d.get("c8y_Availability", {}).get("status") == "AVAILABLE"
        )
        offline = sum(
            1 for d in devices if d.get("c8y_Availability", {}).get("status") == "UNAVAILABLE"
        )
        maintenance = len(devices) - online - offline

        # Fetch alarms for all devices in the group
        params_alarms = {"pageSize": 1000}
        alarms_resp = await self._get("/alarm/alarms", params=params_alarms)
        all_alarms = alarms_resp.get("alarms", [])

        # Filter to only alarms from devices in this group
        device_ids = {d.get("id") for d in devices}
        group_alarms = [a for a in all_alarms if a.get("source", {}).get("id") in device_ids]
        active_alarms = sum(1 for a in group_alarms if a.get("status") == "ACTIVE")
        critical_alarms = sum(
            1
            for a in group_alarms
            if a.get("status") == "ACTIVE" and a.get("severity") == "CRITICAL"
        )

        # Collect device types
        device_types = list({d.get("type") for d in devices if d.get("type")})

        return {
            "group": group_name,
            "group_id": group_id,
            "total_devices": len(devices),
            "online": online,
            "offline": offline,
            "maintenance": maintenance,
            "active_alarms": active_alarms,
            "critical_alarms": critical_alarms,
            "device_types": device_types,
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
        # Attempt to extract group name from custom fields if present
        group = None
        if "c8y_GroupInfo" in raw:
            group = raw["c8y_GroupInfo"].get("name")
        return {
            "id": raw.get("id"),
            "name": raw.get("name"),
            "type": raw.get("type"),
            "status": avail,
            "last_message": raw.get("lastUpdated"),
            "group": group,
        }
