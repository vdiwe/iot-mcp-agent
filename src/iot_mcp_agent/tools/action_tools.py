"""Action-focused tool implementations."""

from typing import Any


class ActionTools:
    """Thin async wrapper around platform write/action operations."""

    def __init__(self, adapter):
        self.adapter = adapter

    async def update_device_config(
        self,
        device_id: str,
        config_key: str,
        config_value: Any,
        reason: str,
    ) -> dict:
        return await self.adapter.update_device_config(
            device_id=device_id,
            config_key=config_key,
            config_value=config_value,
            reason=reason,
        )

    async def send_notification(
        self,
        channel: str,
        recipient: str,
        subject: str,
        message: str,
        priority: str = "normal",
    ) -> dict:
        return await self.adapter.send_notification(
            channel=channel,
            recipient=recipient,
            subject=subject,
            message=message,
            priority=priority,
        )
