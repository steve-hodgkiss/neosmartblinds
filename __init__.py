"""The neosmartblinds component.

This component provides integration for Neo Smart Blinds controllers,
allowing Home Assistant to control blinds through their local API.
"""

import logging
from typing import Final

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_ID, CONF_NAME, CONF_PLATFORM, Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN: Final = "neosmartblinds"
PLATFORMS: list[Platform] = [Platform.COVER]
CONF_DEVICES = "devices"
CONF_BLIND_ID = "blind_id"

# YAML configuration schema for legacy support (domain-based format)
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_ID): cv.string,
                vol.Optional(CONF_NAME, default="Neo Smart Blinds Controller"): cv.string,
                vol.Optional(CONF_DEVICES, default={}): vol.Schema(
                    {cv.string: {vol.Required(CONF_NAME): cv.string}}
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the neosmartblinds component from YAML.

    Detects YAML configuration (both domain-based and platform-based)
    and triggers migration to config entries.

    Args:
        hass: Home Assistant instance
        config: Configuration dictionary

    Returns:
        True if setup was successful
    """
    hass.data.setdefault(DOMAIN, {})

    # Handle domain-based YAML configuration
    if DOMAIN in config:
        yaml_config = config[DOMAIN]
        hass.data[DOMAIN]["yaml_config"] = yaml_config

        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "import"},
                data=yaml_config,
            )
        )
        return True

    # Handle old platform-based configuration (cover: - platform: neosmartblinds)
    if "cover" in config:
        covers = config["cover"]
        if isinstance(covers, list):
            for cover_config in covers:
                if isinstance(cover_config, dict) and cover_config.get(CONF_PLATFORM) == DOMAIN:
                    # Convert platform-based config to domain-based format
                    yaml_config = {
                        CONF_HOST: cover_config.get(CONF_HOST),
                        CONF_ID: cover_config.get(CONF_ID),
                        CONF_NAME: cover_config.get(CONF_NAME, "Neo Smart Blinds Controller"),
                        CONF_DEVICES: cover_config.get(CONF_DEVICES, {}),
                    }
                    hass.data[DOMAIN]["yaml_config"] = yaml_config

                    hass.async_create_task(
                        hass.config_entries.flow.async_init(
                            DOMAIN,
                            context={"source": "import"},
                            data=yaml_config,
                        )
                    )
                    return True

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up neosmartblinds from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry object

    Returns:
        True if setup was successful
    """
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry object

    Returns:
        True if unload was successful
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


