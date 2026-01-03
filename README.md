# Neo Smart Blinds Integration for Home Assistant

A Home Assistant custom integration for controlling Neo Smart Blinds via their local API.

## Features

- Control Neo Smart Blinds covers (open, close, stop)
- UI-based configuration (no YAML required)
- Add/remove blinds without restarting Home Assistant
- Support for multiple blinds on a single controller

## Requirements

- Home Assistant 2021.12 or later
- Neo Smart Blinds Controller with local API access
- Network connectivity between Home Assistant and the controller

## Installation

Copy the `neosmartblinds` folder to `custom_components` in your Home Assistant configuration directory, then restart Home Assistant.

## Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services** → **Create Integration**
2. Search for "Neo Smart Blinds"
3. Enter the following information:
   - **Controller IP Address**: The IP address of your Neo Smart Blinds controller (e.g., `192.168.1.100`)
   - **Controller ID**: The 24-character unique ID of your controller (found on the device)
   - **Controller Name**: A friendly name for this controller (e.g., "Living Room Controller")
4. Click **Next**
5. Add your blinds:
   - **Blind ID**: The unique identifier for each blind (provided by the controller)
   - **Blind Name**: A friendly name (e.g., "Living Room Blinds")
   - Check "Add another blind?" to add more blinds, or uncheck to finish

### Adding or Removing Blinds Later

1. Go to **Settings** → **Devices & Services**
2. Find your Neo Smart Blinds integration
3. Click the menu (⋮) and select **Reconfigure**
4. Modify the controller settings if needed, then click **Next**
5. Manage your blinds:
   - Select **Add a blind** to add a new blind
   - Select **Remove a blind** to remove an existing blind
   - Select **Done** when finished

### Updating Controller Name

1. Go to **Settings** → **Devices & Services**
2. Find your Neo Smart Blinds integration
3. Click the menu (⋮) and select **Reconfigure**
4. Change the **Controller Name** field
5. Click **Next** and then **Done**

## Usage

Once configured, your blinds will appear as cover entities in Home Assistant. You can:

- **Open**: Raise the blinds to full height
- **Close**: Lower the blinds completely
- **Stop**: Stop the blinds at their current position

### Available Services

The integration supports all standard Home Assistant cover services:

- `cover.open_cover` - Open the blind
- `cover.close_cover` - Close the blind
- `cover.stop_cover` - Stop the blind

### Automations and Scripts

You can use your blinds in automations and scripts like any other cover:

```yaml
automation:
  - alias: "Close blinds at sunset"
    trigger:
      sun: event_type: sunset
    action:
      service: cover.close_cover
      target:
        entity_id: cover.living_room_blinds
```

## Finding Your Controller Information

### Controller IP Address

1. Access your router's admin panel
2. Look for connected devices on your network
3. Find your Neo Smart Blinds controller and note its IP address

Or use network scanning tools like:

- `ping neosmartblinds.local` (if mDNS is enabled)
- Network scanner apps on your phone

### Controller ID

The 24-character controller ID is typically:

- Printed on the device label
- Available in the Neo Smart Blinds mobile app settings
- Viewable in your router's connected devices list

### Blind IDs

Blind IDs are assigned by the controller. You may need to:

- Check the Neo Smart Blinds mobile app
- Refer to your controller documentation
- Check controller logs or status page

## Troubleshooting

### Integration won't add

- Verify the Controller IP address is correct
- Ensure your Home Assistant can reach the controller on your network
- Check that the Controller ID is exactly 24 characters

### Blinds don't respond

- Verify the Blind IDs are correct
- Check that the blinds are paired with the controller
- Ensure the controller is powered on and connected to the network
- Check Home Assistant logs for error messages

### Entity won't delete after removal

The entity will be removed from Home Assistant's registry when you next restart Home Assistant or reconfigure the integration.

## Support

For issues or feature requests, please visit the GitHub repository or check the Home Assistant community forums.

## API Information

The integration communicates with the Neo Smart Blinds controller using the following API format:

```
http://{controller_ip}:8838/neo/v1/transmit?command={blind_id}-{command}&id={controller_id}
```

Where:

- `{controller_ip}`: IP address of the controller
- `{blind_id}`: Unique identifier of the blind
- `{command}`: One of `up`, `dn`, or `sp` (up, down, stop)
- `{controller_id}`: 24-character controller ID

## License

This integration is provided as-is for personal use.
