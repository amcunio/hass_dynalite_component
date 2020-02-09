"""Code to handle a Dynalite bridge."""
import pprint
import asyncio

from dynalite_devices_lib import DynaliteDevices, DOMAIN as DYNDOMAIN
from dynalite_lib import CONF_ALL

from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr, area_registry as ar
from homeassistant.const import CONF_HOST

from .const import (
    DOMAIN,
    DATA_CONFIGS,
    LOGGER,
    CONF_AREACREATE,
    CONF_AREACREATE_MANUAL,
    CONF_AREACREATE_ASSIGN,
    CONF_AREACREATE_AUTO,
    ENTITY_CATEGORIES,
)


from .light import DynaliteLight
from .switch import DynaliteSwitch
from .cover import DynaliteCover, DynaliteCoverWithTilt


class BridgeError(Exception):
    """Class to throw exceptions from DynaliteBridge."""

    def __init__(self, message):
        """Initialize the exception."""
        super().__init__()
        self.message = message


class DynaliteBridge:
    """Manages a single Dynalite bridge."""

    def __init__(self, hass, config_entry):
        """Initialize the system based on host parameter."""
        self.config_entry = config_entry
        self.hass = hass
        self.area = {}
        self.async_add_entities = {}
        self.waiting_entities = {}
        self.all_entities = {}
        self.area_reg = None
        self.device_reg = None
        self.config = None
        self.host = config_entry.data[CONF_HOST]
        if self.host not in hass.data[DOMAIN][DATA_CONFIGS]:
            LOGGER.info("invalid host - %s", self.host)
            raise BridgeError("invalid host - " + self.host)
        self.config = hass.data[DOMAIN][DATA_CONFIGS][self.host]
        # Configure the dynalite devices
        self.dynalite_devices = DynaliteDevices(
            config=self.config,
            newDeviceFunc=self.add_devices,
            updateDeviceFunc=self.update_device,
        )

    async def async_setup(self, tries=0):
        """Set up a Dynalite bridge based on host parameter."""
        LOGGER.debug(
            "component bridge async_setup - %s" % pprint.pformat(self.config_entry.data)
        )
        self.area_reg = await ar.async_get_registry(self.hass)
        self.device_reg = await dr.async_get_registry(self.hass)
        # Configure the dynalite devices
        await self.dynalite_devices.async_setup()
        for category in ENTITY_CATEGORIES:
            self.hass.async_create_task(
                self.hass.config_entries.async_forward_entry_setup(
                    self.config_entry, category
                )
            )
        return True

    @callback
    def add_devices(self, devices):
        """Call when devices should be added to home assistant."""
        added_entities = {}
        for category in ENTITY_CATEGORIES:
            added_entities[category] = []

        for device in devices:
            category = device.category
            if category == "light":
                entity = DynaliteLight(device, self)
            elif category == "switch":
                entity = DynaliteSwitch(device, self)
            elif category == "cover":
                if device.has_tilt:
                    entity = DynaliteCoverWithTilt(device, self)
                else:
                    entity = DynaliteCover(device, self)
            else:
                LOGGER.debug("Illegal device category %s", category)
                continue
            added_entities[category].append(entity)
            self.all_entities[entity.unique_id] = entity

        for category in ENTITY_CATEGORIES:
            if added_entities[category]:
                self.add_entities_when_registered(category, added_entities[category])

    @callback
    def update_device(self, device):
        """Call when a device or all devices should be updated."""
        if device == CONF_ALL:
            # This is used to signal connection or disconnection, so all devices may become available or not.
            if self.dynalite_devices.available:
                LOGGER.info("Connected to dynalite host")
            else:
                LOGGER.info("Disconnected from dynalite host")
            for uid in self.all_entities:
                self.all_entities[uid].try_schedule_ha()
        else:
            uid = device.unique_id
            if uid in self.all_entities:
                self.all_entities[uid].try_schedule_ha()

    @callback
    def register_add_entities(self, category, async_add_entities):
        """Add an async_add_entities for a category."""
        self.async_add_entities[category] = async_add_entities
        if category in self.waiting_entities:
            self.async_add_entities[category](self.waiting_entities[category])

    def add_entities_when_registered(self, category, entities):
        """Add the entities to ha if async_add_entities was registered, otherwise queue until it is."""
        if not entities:
            return
        if category in self.async_add_entities:
            self.async_add_entities[category](entities)
        else:  # handle it later when it is registered
            if category not in self.waiting_entities:
                self.waiting_entities[category] = []
            self.waiting_entities[category].extend(entities)

    async def async_reset(self):
        """Reset this bridge to default state.

        Will cancel any scheduled setup retry and will unload
        the config entry.
        """
        results = await asyncio.gather(
            self.hass.config_entries.async_forward_entry_unload(
                self.config_entry, "light"
            ),
            self.hass.config_entries.async_forward_entry_unload(
                self.config_entry, "switch"
            ),
            self.hass.config_entries.async_forward_entry_unload(
                self.config_entry, "cover"
            ),
        )
        # None and True are OK
        return False not in results

    async def entity_added_to_ha(self, entity):
        """Call when an entity is added to HA so we can set its area."""
        areacreate = self.config.get(CONF_AREACREATE)
        if areacreate and areacreate.lower() == CONF_AREACREATE_MANUAL:
            LOGGER.debug("area assignment set to manual - ignoring")
            return  # only need to update the areas if it is 'assign' or 'create'
        if areacreate not in [CONF_AREACREATE_ASSIGN, CONF_AREACREATE_AUTO]:
            LOGGER.debug(
                CONF_AREACREATE
                + ' has unknown value of %s - assuming "'
                + CONF_AREACREATE_MANUAL
                + '" and ignoring',
                areacreate,
            )
            return
        uniqueID = entity.unique_id
        hassArea = entity.get_hass_area
        if hassArea != "":
            LOGGER.debug("assigning hass area %s to entity %s" % (hassArea, uniqueID))
            device = self.device_reg.async_get_device({(DYNDOMAIN, uniqueID)}, ())
            if not device:
                LOGGER.error("uniqueID %s has no device ID", uniqueID)
                return
            areaEntry = self.area_reg._async_is_registered(hassArea)
            if not areaEntry:
                if areacreate != CONF_AREACREATE_AUTO:
                    LOGGER.debug(
                        "Area %s not registered and "
                        + CONF_AREACREATE
                        + ' is not "'
                        + CONF_AREACREATE_AUTO
                        + '" - ignoring',
                        hassArea,
                    )
                    return
                else:
                    LOGGER.debug("Creating new area %s", hassArea)
                    areaEntry = self.area_reg.async_create(hassArea)
            LOGGER.debug("assigning deviceid=%s area_id=%s" % (device.id, areaEntry.id))
            self.device_reg.async_update_device(device.id, area_id=areaEntry.id)
