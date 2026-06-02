"""Device-focused tool implementations."""

from typing import Any


class DeviceTools:
    """Thin async wrapper around platform device operations."""

    def __init__(self, adapter: Any):
        self.adapter = adapter

    async def list_devices(
        self,
        group: str | None = None,
        device_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> dict:
        return await self.adapter.list_devices(
            group=group,
            device_type=device_type,
            status=status,
            limit=limit,
        )

    async def get_device(self, device_id: str) -> dict:
        return await self.adapter.get_device(device_id)

    async def get_measurements(
        self,
        device_id: str,
        measurement_type: str | None = None,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int = 100,
    ) -> dict:
        return await self.adapter.get_measurements(
            device_id=device_id,
            measurement_type=measurement_type,
            from_time=from_time,
            to_time=to_time,
            limit=limit,
        )

    async def get_device_group_summary(self, group_name: str) -> dict:
        return await self.adapter.get_device_group_summary(group_name)
