"""Config flow for Neo Smart Blinds integration.

Handles user configuration, reconfiguration, and blind management
through a multi-step UI flow.
"""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_ID
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "neosmartblinds"
CONF_DEVICES = "devices"
CONF_BLIND_ID = "blind_id"


class NeoSmartBlindsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Neo Smart Blinds.

    Manages the initial setup, reconfiguration, and blind management
    for Neo Smart Blinds controllers.
    """

    VERSION = 1
    _controller_data: Dict[str, Any] = {}
    _devices: Dict[str, Dict[str, str]] = {}

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step - controller configuration.
        
        Prompts user for controller IP, ID, and name, then moves to blind setup.
        
        Args:
            user_input: User input from the form
            
        Returns:
            FlowResult with form or next step
        """
        errors = {}

        if user_input is not None:
            # Store controller data and move to blind setup
            self._controller_data = user_input
            self._devices = {}
            return await self.async_step_add_blinds()

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_ID): cv.string,
                vol.Optional(CONF_NAME, default="Neo Smart Blinds Controller"): cv.string,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reconfigure(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle reconfiguration of the integration.

        Allows users to update controller settings and manage blinds
        after the initial setup.

        Args:
            user_input: User input from the form

        Returns:
            FlowResult with the next step or abort
        """
        config_entry = self.hass.config_entries.async_get_entry(
            self.context.get("entry_id")
        )

        if config_entry is None:
            return self.async_abort(reason="reconfigure_failed")

        if user_input is not None:
            # User submitted new controller config
            self._controller_data = {
                CONF_HOST: user_input.get(CONF_HOST, config_entry.data.get(CONF_HOST)),
                CONF_ID: user_input.get(CONF_ID, config_entry.data.get(CONF_ID)),
                CONF_NAME: user_input.get(CONF_NAME, config_entry.data.get(CONF_NAME)),
            }
            # Load existing devices
            self._devices = dict(config_entry.data.get(CONF_DEVICES, {}))
            return await self.async_step_manage_blinds()

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=config_entry.data.get(CONF_HOST)): cv.string,
                vol.Required(CONF_ID, default=config_entry.data.get(CONF_ID)): cv.string,
                vol.Optional(CONF_NAME, default=config_entry.data.get(CONF_NAME, "Neo Smart Blinds Controller")): cv.string,
            }
        )

        return self.async_show_form(step_id="reconfigure", data_schema=schema)

    async def async_step_add_blinds(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle adding individual blinds during initial setup.

        Allows users to add one or more blinds to the controller
        during the initial setup process.

        Args:
            user_input: User input from the form

        Returns:
            FlowResult with the next step, retry, or entry creation
        """
        errors = {}

        if user_input is not None:
            blind_id = user_input.get(CONF_BLIND_ID)
            blind_name = user_input.get(CONF_NAME)

            # Add the blind to devices
            if blind_id and blind_name:
                self._devices[blind_id] = {CONF_NAME: blind_name}

            # Ask if user wants to add more blinds
            if user_input.get("add_another", False):
                return await self.async_step_add_blinds()

            # Finalize the config entry
            if self._devices:
                config_data = {**self._controller_data, CONF_DEVICES: self._devices}

                # Check if entry already exists
                await self.async_set_unique_id(self._controller_data.get(CONF_HOST))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=self._controller_data.get(CONF_NAME, "Neo Smart Blinds Controller"),
                    data=config_data,
                )
            else:
                # No blinds added, go back to add blinds step
                return await self.async_step_add_blinds()

        # Show form for adding a blind
        blind_list = (
            "\n".join(
                [f"  • {bid}: {info[CONF_NAME]}" for bid, info in self._devices.items()]
            )
            if self._devices
            else "  None yet"
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_BLIND_ID): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Optional("add_another", default=True): cv.boolean,
            }
        )

        description_placeholders = {
            "blinds_list": blind_list,
        }

        return self.async_show_form(
            step_id="add_blinds",
            data_schema=schema,
            description_placeholders=description_placeholders,
            errors=errors,
        )

    async def async_step_manage_blinds(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle managing blinds during reconfiguration.

        Allows users to add or remove blinds from an existing controller
        during reconfiguration.

        Args:
            user_input: User input from the form

        Returns:
            FlowResult with the next step or abort
        """
        errors = {}

        if user_input is not None:
            action = user_input.get("action")
            blind_id = user_input.get(CONF_BLIND_ID, "").strip()
            blind_name = user_input.get(CONF_NAME, "").strip()

            if action == "add":
                if not blind_id or not blind_name:
                    errors["base"] = "invalid_blind"
                elif blind_id in self._devices:
                    errors["base"] = "blind_already_exists"
                else:
                    self._devices[blind_id] = {CONF_NAME: blind_name}
                    return await self.async_step_manage_blinds()
            elif action == "remove":
                if blind_id and blind_id in self._devices:
                    del self._devices[blind_id]
                    return await self.async_step_manage_blinds()
            elif action == "done":
                # Update the existing entry
                config_entry = self.hass.config_entries.async_get_entry(
                    self.context.get("entry_id")
                )
                if config_entry:
                    self.hass.config_entries.async_update_entry(
                        config_entry,
                        title=self._controller_data.get(CONF_NAME, "Neo Smart Blinds"),
                        data={**self._controller_data, CONF_DEVICES: self._devices},
                    )
                    await self.hass.config_entries.async_reload(config_entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")

        # Show current blinds
        blind_list = (
            "\n".join(
                [f"  • {bid}: {info[CONF_NAME]}" for bid, info in self._devices.items()]
            )
            if self._devices
            else "  None configured"
        )

        schema = vol.Schema(
            {
                vol.Required("action"): vol.In({
                    "add": "Add a blind",
                    "remove": "Remove a blind",
                    "done": "Done",
                }),
                vol.Optional(CONF_BLIND_ID): cv.string,
                vol.Optional(CONF_NAME): cv.string,
            }
        )

        return self.async_show_form(
            step_id="manage_blinds",
            data_schema=schema,
            description_placeholders={"blinds_list": blind_list},
            errors=errors,
        )

    async def async_step_import(self, import_data: Dict[str, Any]) -> FlowResult:
        """Handle import from YAML configuration.

        Automatically creates a config entry from YAML configuration,
        allowing users to migrate from configuration.yaml.

        Args:
            import_data: Data from YAML configuration

        Returns:
            FlowResult with created entry or abort
        """
        # Check if entry already exists for this host
        host = import_data.get(CONF_HOST)
        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()

        # Create config entry from YAML
        config_data = {
            CONF_HOST: host,
            CONF_ID: import_data.get(CONF_ID),
            CONF_NAME: import_data.get(CONF_NAME, "Neo Smart Blinds Controller"),
            CONF_DEVICES: import_data.get(CONF_DEVICES, {}),
        }

        _LOGGER.info(
            "Importing Neo Smart Blinds configuration from YAML for host %s", host
        )

        return self.async_create_entry(
            title=config_data.get(CONF_NAME, "Neo Smart Blinds Controller"),
            data=config_data,
        )

