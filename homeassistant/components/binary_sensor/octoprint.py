"""
Support for monitoring OctoPrint binary sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.octoprint/
"""
import logging

import requests
import voluptuous as vol

from homeassistant.const import (
    CONF_NAME, STATE_ON, STATE_OFF, CONF_MONITORED_CONDITIONS)
from homeassistant.components.binary_sensor import (
    BinarySensorDevice, PLATFORM_SCHEMA)
from homeassistant.loader import get_component
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['octoprint']

DEFAULT_NAME = 'OctoPrint'

SENSOR_TYPES = {
    # API Endpoint, Group, Key, unit
    'Printing': ['printer', 'state', 'printing', None],
    'Printing Error': ['printer', 'state', 'error', None]
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_MONITORED_CONDITIONS, default=SENSOR_TYPES):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the available OctoPrint binary sensors."""
    octoprint = get_component('octoprint')
    name = config.get(CONF_NAME)
    monitored_conditions = config.get(CONF_MONITORED_CONDITIONS,
                                      SENSOR_TYPES.keys())

    devices = []
    for octo_type in monitored_conditions:
        new_sensor = OctoPrintBinarySensor(octoprint.OCTOPRINT,
                                           octo_type,
                                           SENSOR_TYPES[octo_type][2],
                                           name,
                                           SENSOR_TYPES[octo_type][3],
                                           SENSOR_TYPES[octo_type][0],
                                           SENSOR_TYPES[octo_type][1],
                                           'flags')
        devices.append(new_sensor)
    add_devices(devices)


class OctoPrintBinarySensor(BinarySensorDevice):
    """Representation an OctoPrint binary sensor."""

    def __init__(self, api, condition, sensor_type, sensor_name, unit,
                 endpoint, group, tool=None):
        """Initialize a new OctoPrint sensor."""
        self.sensor_name = sensor_name
        if tool is None:
            self._name = '{} {}'.format(sensor_name, condition)
        else:
            self._name = '{} {}'.format(sensor_name, condition)
        self.sensor_type = sensor_type
        self.api = api
        self._state = False
        self._unit_of_measurement = unit
        self.api_endpoint = endpoint
        self.api_group = group
        self.api_tool = tool
        # Set initial state
        self.update()
        _LOGGER.debug("Created OctoPrint binary sensor %r", self)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.is_on

    @property
    def is_on(self):
        """Return true if binary sensor is on."""
        if self._state:
            return STATE_ON
        else:
            return STATE_OFF

    @property
    def sensor_class(self):
        """Return the class of this sensor, from SENSOR_CLASSES."""
        return None

    def update(self):
        """Update state of sensor."""
        try:
            self._state = self.api.update(self.sensor_type,
                                          self.api_endpoint,
                                          self.api_group,
                                          self.api_tool)
        except requests.exceptions.ConnectionError:
            # Error calling the api, already logged in api.update()
            return

        if self._state is None:
            _LOGGER.warning("Unable to locate value for %s", self.sensor_type)
