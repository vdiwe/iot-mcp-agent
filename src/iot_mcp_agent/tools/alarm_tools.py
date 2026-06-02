"""Alarm-focused tool implementations."""


class AlarmTools:
    """Thin async wrapper around platform alarm operations."""

    def __init__(self, adapter):
        self.adapter = adapter

    async def get_alarms(
        self,
        device_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> dict:
        return await self.adapter.get_alarms(
            device_id=device_id,
            severity=severity,
            status=status,
            limit=limit,
        )

    async def create_alarm(
        self,
        device_id: str,
        type: str,
        severity: str,
        text: str,
    ) -> dict:
        return await self.adapter.create_alarm(
            device_id=device_id,
            type=type,
            severity=severity,
            text=text,
        )
