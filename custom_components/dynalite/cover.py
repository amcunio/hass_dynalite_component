"""Support for the Dynalite channels as switches."""
import asyncio
import logging
from .const import DOMAIN, LOGGER, DATA_CONFIGS
import pprint

from homeassistant.const import CONF_COVERS
from homeassistant.components.cover import CoverDevice
from .dynalitebase import async_setup_channel_entry, DynaliteChannelBase

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way.

    """
    pass


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Records the async_add_entities function to add them later when received from Dynalite."""
    async_setup_channel_entry('cover', hass, config_entry, async_add_entities)

class DynaliteChannelCover(DynaliteChannelBase, CoverDevice):
    """Representation of a Dynalite Channel as a Home Assistant Cover."""

    def __init__(self, area, channel, name, type, cover_factor, bridge, device):
        """Initialize the light."""
        self._area = area
        self._channel = channel
        self._name = name
        self._type = type
        self._cover_factor = cover_factor
        self._actual_level = 0
        self._target_level = 0
        self._current_position = 0
        self._bridge = bridge
        self._device = device

    def update_level(self, actual_level, target_level):
        prev_actual_level = self._actual_level
        self._actual_level = actual_level
        self._target_level = target_level
        level_diff = actual_level - prev_actual_level
        factored_diff = level_diff / self._cover_factor
        self._current_position = min(1, max(0, self._current_position + factored_diff))
        if self._current_position > 0.99999:
            self._current_position = 1
        if self._current_position < 0.00001:
            self._current_position = 0
        
    @property
    def current_cover_position(self):
        """return the position of the cover from 0 to 100"""
        return int(self._current_position*100)

    @property
    def is_opening(self):
        return self._target_level > self._actual_level
        
    @property
    def is_closing(self):
        return self._target_level < self._actual_level
        
    @property
    def is_closed(self):
        return self._current_position == 0

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        self._device.turnOn()
        
    async def async_close_cover(self, **kwargs):
        """Open the cover."""
        self._device.turnOff()

    async def async_set_cover_position(self, **kwargs):
        """Open the cover."""
        target_position = kwargs['position'] / 100
        position_diff = target_position - self._current_position
        level_diff = position_diff * self._cover_factor
        target_level = min(1, max(0, self._actual_level + level_diff))
        self._device.turnOn(brightness = target_level)
        
    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        self._device.stopFade()