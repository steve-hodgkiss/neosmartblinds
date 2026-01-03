"""Device actions for Neo Smart Blinds integration.

Provides device action handlers for automations, allowing users to
perform blind control actions through the device interface.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.device_automation import (
    ACTION_TYPE_SCHEMA,
)
from homeassistant.components.cover import (
    ATTR_POSITION,
    SERVICE_OPEN_COVER,
    SERVICE_CLOSE_COVER,
    SERVICE_STOP_COVER,
    SERVICE_SET_COVER_POSITION,
)
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry, async_entries_for_device

_LOGGER = logging.getLogger(__name__)

DOMAIN = "neosmartblinds"

ACTION_TYPE_OPEN = "open"
ACTION_TYPE_CLOSE = "close"
ACTION_TYPE_STOP = "stop"
ACTION_TYPE_SET_POSITION = "set_position"

CONF_POSITION = "position"

ACTION_SCHEMA = ACTION_TYPE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(
            [
                ACTION_TYPE_OPEN,
                ACTION_TYPE_CLOSE,
                ACTION_TYPE_STOP,
                ACTION_TYPE_SET_POSITION,
            ]
        ),
        vol.Optional(CONF_POSITION): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
    }
)


async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device actions for Neo Smart Blinds.
    
    Args:
        hass: Home Assistant instance
        device_id: Device ID to get actions for
        
    Returns:
        List of available device actions
    """
    registry: EntityRegistry = hass.helpers.entity_registry.async_get(hass)
    actions = []

    # Get all entities for this device
    for entry in async_entries_for_device(registry, device_id):
        if entry.domain == "cover":
            actions.extend(
                [
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.entity_id,
                        CONF_TYPE: ACTION_TYPE_OPEN,
                    },
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.entity_id,
                        CONF_TYPE: ACTION_TYPE_CLOSE,
                    },
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.entity_id,
                        CONF_TYPE: ACTION_TYPE_STOP,
                    },
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.entity_id,
                        CONF_TYPE: ACTION_TYPE_SET_POSITION,
                    },
                ]
            )

    return actions


async def async_call_action_from_config(
    hass: HomeAssistant,
    config: dict[str, Any],
    variables: dict[str, Any],
    context: Context | None = None,
) -> None:
    """Execute a device action.
    
    Args:
        hass: Home Assistant instance
        config: Action configuration
        variables: Template variables
        context: Execution context
    """
    action_type = config[CONF_TYPE]
    entity_id = config[CONF_ENTITY_ID]

    service_data = {CONF_ENTITY_ID: entity_id}

    if action_type == ACTION_TYPE_OPEN:
        await hass.services.async_call(
            "cover", SERVICE_OPEN_COVER, service_data, context=context
        )
    elif action_type == ACTION_TYPE_CLOSE:
        await hass.services.async_call(
            "cover", SERVICE_CLOSE_COVER, service_data, context=context
        )
    elif action_type == ACTION_TYPE_STOP:
        await hass.services.async_call(
            "cover", SERVICE_STOP_COVER, service_data, context=context
        )
    elif action_type == ACTION_TYPE_SET_POSITION:
        service_data[ATTR_POSITION] = config.get(CONF_POSITION, 50)
        await hass.services.async_call(
            "cover", SERVICE_SET_COVER_POSITION, service_data, context=context
        )


async def async_get_action_capabilities(
    hass: HomeAssistant, config: dict[str, Any]
) -> dict[str, Any]:
    """Get action capabilities.
    
    Args:
        hass: Home Assistant instance
        config: Action configuration
        
    Returns:
        Action capabilities schema
    """
    action_type = config[CONF_TYPE]

    if action_type == ACTION_TYPE_SET_POSITION:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required(CONF_POSITION): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=100)
                    )
                }
            )
        }

    return {}
