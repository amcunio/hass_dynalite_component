"""Support for the Dynalite channels and presets as switches."""
import asyncio
import logging
from .const import DOMAIN, LOGGER
import pprint

from .dynalitebase import async_setup_channel_entry, DynaliteChannelBase, DynaliteBase
from homeassistant.components.switch import SwitchDevice
from homeassistant.core import callback

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way.

    """
    pass


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Records the async_add_entities function to add them later when received from Dynalite."""
    async_setup_channel_entry('switch', hass, config_entry, async_add_entities)

class DynaliteChannelSwitch(DynaliteChannelBase, SwitchDevice):
    """Representation of a Dynalite Channel as a Home Assistant Switch."""

    def __init__(self, area, channel, name, type, hass_area, bridge, device):
        """Initialize the switch."""
        self._area = area
        self._channel = channel
        self._name = name
        self._type = type
        self._hass_area = hass_area
        self._level = 0
        self._bridge = bridge
        self._device = device

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._level > 0

    @callback
    def update_level(self, actual_level, target_level):
        self._level = actual_level

    async def async_turn_on(self, **kwargs):
        self._device.turnOn()

    async def async_turn_off(self, **kwargs):
        self._device.turnOff()

class DynalitePresetSwitch(DynaliteBase, SwitchDevice):
    """Representation of a Dynalite Preset as a Home Assistant Switch."""

    def __init__(self, area, preset, name, hass_area, bridge, device):
        """Initialize the switch."""
        self._area = area
        self._preset = preset
        self._name = name
        self._hass_area = hass_area
        self._level = 0
        self._bridge = bridge
        self._device = device

    @property
    def unique_id(self):
        """Return the ID of this cover."""
        return "dynalite_area_"+str(self._area)+"_preset_"+str(self._preset)

    @property
    def is_on(self):
        """Return true if device is on."""
        new_level = self._device.active
        if new_level != self._level:
            self.update_listeners()
        self._level = new_level
        return self._level

    @callback
    def update_level(self, actual_level, target_level):
        self._level = actual_level

    async def async_turn_on(self, **kwargs):
        self._device.turnOn()

    async def async_turn_off(self, **kwargs):
        self._device.turnOff()

class DynaliteRoomPresetSwitch(DynaliteBase, SwitchDevice):
    """Representation of a Dynalite Preset as a Home Assistant Switch."""

    def __init__(self, area, name, hass_area, bridge):
        """Initialize the switch."""
        self._area = area
        self._name = name
        self._hass_area = hass_area
        self._bridge = bridge
        self._device_on = None
        self._device_off = None

    @property
    def available(self):
        """Return if cover is available."""
        return self._device_on and self._device_off

    @property
    def unique_id(self):
        """Return the ID of this cover."""
        return "dynalite_area_"+str(self._area)+"_room_switch"

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._device_on.is_on

    async def async_turn_on(self, **kwargs):
        await self._device_on.async_turn_on()

    async def async_turn_off(self, **kwargs):
        await self._device_off.async_turn_on()
        
    @callback
    def set_device(self, device_on=None, device_off=None):
        if device_on:
            self._device_on = device_on
            device_on.add_listener(self.listener)
        if device_off:
            self._device_off = device_off
            device_off.add_listener(self.listener)
        if self._device_on and self._device_off:
            if self.hass: # if it was not added yet to ha, need to update. will be updated when added to ha
                self.schedule_update_ha_state()
            
    @callback
    def listener(self):
        if self.hass:
            self.schedule_update_ha_state()
