"""Support for NeoSmartBlinds covers.

This module provides cover entities for controlling Neo Smart Blinds
through their local HTTP API. It handles setup, entity management,
and communication with the controller.
"""

import logging
from typing import Any

import requests

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
    CoverDeviceClass,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_ID,
    CONF_DEVICES,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import entity_registry as er

_LOGGER = logging.getLogger(__name__)

DOMAIN = "neosmartblinds"
supported_features = (
    CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NeoSmartBlinds covers from config entry.

    Creates cover entities for each configured blind and removes
    entities for blinds that have been deleted from the configuration.

    Args:
        hass: Home Assistant instance
        config_entry: Config entry object
        async_add_entities: Callback to add new entities
    """
    config_data = config_entry.data
    controller_host = config_data.get(CONF_HOST)
    controller_id = config_data.get(CONF_ID)
    devices = config_data.get(CONF_DEVICES, {})

    # Clean up removed entities from entity registry
    entity_registry = er.async_get(hass)
    for entity_id in list(entity_registry.entities):
        entity_entry = entity_registry.entities[entity_id]
        if (
            entity_entry.config_entry_id == config_entry.entry_id
            and entity_entry.domain == "cover"
        ):
            # Extract blind_id from unique_id
            unique_id = entity_entry.unique_id
            if unique_id and unique_id.startswith(f"{DOMAIN}_"):
                blind_id = unique_id.split("_", 2)[2]  # Extract blind_id from unique_id
                if blind_id not in devices:
                    # Blind was removed, delete the entity
                    entity_registry.async_remove(entity_id)
                    _LOGGER.info("Removed entity for blind %s", blind_id)

    covers = []
    if devices:
        for blind_id, entity_info in devices.items():
            name = entity_info.get(CONF_NAME)
            _LOGGER.info("Adding %s neosmartblinds cover", name)
            cover = NeoSmartBlindsCover(
                hass=hass,
                blind_id=blind_id,
                name=name,
                controller_host=controller_host,
                controller_id=controller_id,
                config_entry=config_entry,
            )
            covers.append(cover)

    if covers:
        async_add_entities(covers)
    else:
        _LOGGER.warning("No covers configured for entry")


class NeoSmartBlindsCover(CoverEntity):
    """Representation of NeoSmartBlinds cover.

    Provides control over a single blind via the Neo Smart Blinds
    controller API.
    """

    _attr_supported_features = supported_features
    _attr_device_class = CoverDeviceClass.BLIND

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        controller_host: str,
        blind_id: str,
        controller_id: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the cover.

        Args:
            hass: Home Assistant instance
            name: Friendly name for the blind
            controller_host: IP address of the controller
            blind_id: Unique identifier for the blind
            controller_id: 24-character controller ID
            config_entry: Config entry object
        """
        self._blind_id = blind_id
        self._hass = hass
        self._name = name
        self._controller_host = controller_host
        self._controller_id = controller_id
        self._available = True
        self._is_closed: bool | None = None
        self._config_entry = config_entry

    @property
    def name(self) -> str:
        """Return the name of the cover."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique id for the entity."""
        return f"{DOMAIN}_{self._config_entry.entry_id}_{self._blind_id}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def is_closed(self) -> bool | None:
        """Return the closed state of the blind.
        
        Returns None as the controller does not report blind position.
        """
        return self._is_closed

    @property
    def should_poll(self) -> bool:
        """Return the polling state. No polling available from controller."""
        return False

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        controller_name = self._config_entry.data.get(CONF_NAME, "Neo Smart Blinds Controller")
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=controller_name,
            manufacturer="Neo Smart Blinds",
            model="Controller",
        )

    def close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        self._move_cover(command="dn")

    def open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        self._move_cover(command="up")

    def stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        self._move_cover(command="sp")

    def _move_cover(self, command: str) -> bool:
        """Build the URI and execute the blind command.

        Makes an HTTP GET request to the controller to send a command
        to the blind. Updates the availability status based on success.

        Args:
            command: Command to send ('up', 'dn', or 'sp')

        Returns:
            True on completion (success or failure)
        """
        httpuri = f"http://{self._controller_host}:8838/neo/v1/transmit?command={self._blind_id}-{command}&id={self._controller_id}"
        try:
            request = requests.get(httpuri, timeout=10)
            if request.status_code != 200:
                response = f"{request.status_code}: {request.text}"
                _LOGGER.error(
                    "Error executing command on %s: %s-%s - Status: %s",
                    self._controller_host,
                    self._blind_id,
                    command,
                    response,
                )
                self._available = False
            else:
                self._available = True
        except requests.exceptions.RequestException as err:
            _LOGGER.error(
                "Error connecting to controller %s: %s",
                self._controller_host,
                err,
            )
            self._available = False
        return True
