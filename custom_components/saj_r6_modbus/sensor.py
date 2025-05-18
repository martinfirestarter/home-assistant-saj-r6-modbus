"""Sensor Platform Device for SAJ R6 Inverter Modbus."""

from __future__ import annotations
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity
import logging
from datetime import datetime
from abc import ABC, abstractmethod

from homeassistant.const import CONF_NAME

from .const import (
    ATTR_MANUFACTURER,
    TOTAL_SENSOR_TYPES,
    DAY_SENSOR_TYPES,
    MONTH_SENSOR_TYPES,
    YEAR_SENSOR_TYPES,
    DOMAIN,
    SENSOR_TYPES,
    SajModbusSensorEntityDescription,
)

from .hub import SAJModbusHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up entry for hub."""
    hub_name = entry.data[CONF_NAME]
    hub = hass.data[DOMAIN][hub_name]["hub"]

    device_data = hub.inverter_data
    device_info = {
        "identifiers": {(DOMAIN, hub_name)},
        "name": hub_name,
        "manufacturer": ATTR_MANUFACTURER,
        "sw_version": device_data["dv"],
        "hw_version": device_data["mcv"],
        "serial_number": device_data["sn"],
    }

    entities = []
    for sensor_description in SENSOR_TYPES.values():
        sensor = SajSensor(
            hub_name,
            hub,
            device_info,
            sensor_description,
        )
        entities.append(sensor)
    for sensor_description in TOTAL_SENSOR_TYPES.values():
        sensor = SajTotalSensor(
            hub_name,
            hub,
            device_info,
            sensor_description,
        )
        entities.append(sensor)
    for sensor_description in DAY_SENSOR_TYPES.values():
        sensor = SajDaySensor(
            hub_name,
            hub,
            device_info,
            sensor_description,
        )
        entities.append(sensor)
    for sensor_description in MONTH_SENSOR_TYPES.values():
        sensor = SajMonthSensor(
            hub_name,
            hub,
            device_info,
            sensor_description,
        )
        entities.append(sensor)
    for sensor_description in YEAR_SENSOR_TYPES.values():
        sensor = SajYearSensor(
            hub_name,
            hub,
            device_info,
            sensor_description,
        )
        entities.append(sensor)

    async_add_entities(entities)
    return True


class SajSensor(CoordinatorEntity, SensorEntity):
    """Representation of an SAJ R6 Modbus sensor."""

    def __init__(
        self,
        platform_name: str,
        hub: SAJModbusHub,
        device_info,
        description: SajModbusSensorEntityDescription,
    ):
        """Initialize the sensor."""
        self._platform_name = platform_name
        self._attr_device_info = device_info
        self.entity_description: SajModbusSensorEntityDescription = description

        super().__init__(coordinator=hub)

    @property
    def device_info(self):
        return self._attr_device_info

    @property
    def name(self):
        """Return the name."""
        return f"{self._platform_name} {self.entity_description.name}"

    @property
    def unique_id(self) -> str | None:
        """Return unique ID for sensor."""
        return f"{self._platform_name}_{self.entity_description.key}"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return self.coordinator.data.get(self.entity_description.key, None)


class SajTotalSensor(SajSensor):
    """Representation of a SAJ Modbus total sensor."""

    def __init__(
        self,
        platform_name: str,
        hub: SAJModbusHub,
        device_info,
        description: SajModbusSensorEntityDescription,
    ):
        """Initialize the sensor."""
        self._last_value = None

        super().__init__(platform_name=platform_name, hub=hub, device_info=device_info, description=description)

    @property
    def native_value(self):
        """Return the value of the sensor."""
        # Return last known value if current value is missing.
        key = self.entity_description.key
        value = None

        if self.coordinator.data.get(key):
            value = self.coordinator.data.get(key)

        if value is not None:
            self._last_value = value
            return value

        return self._last_value

class SajDatetimeSensor(SajSensor, ABC):
    """Representation of a SAJ Modbus day sensor."""

    def __init__(
        self,
        platform_name: str,
        hub: SAJModbusHub,
        device_info,
        description: SajModbusSensorEntityDescription,
    ):
        """Initialize the sensor."""
        self._last_value = None
        self._last_datetime = None

        super().__init__(platform_name=platform_name, hub=hub, device_info=device_info, description=description)

    @abstractmethod
    def _same(self, dt1: datetime, dt2: datetime) -> bool:
        pass

    @property
    def native_value(self):
        """Return the value of the sensor."""
        # Return last known value if current value is missing.
        # Reset to 0 if current value is missing and current datetime is not same as last.
        now = datetime.now()
        key = self.entity_description.key
        value = None

        if self.coordinator.data.get(key):
            value = self.coordinator.data.get(key)

        if value is not None:
            self._last_datetime = now
            self._last_value = value
            return value
        elif not self._same(self._last_datetime, now):
                self._last_value = 0

        return self._last_value
    
class SajDaySensor(SajDatetimeSensor):
    """Representation of a SAJ Modbus day sensor."""

    def __init__(
        self,
        platform_name: str,
        hub: SAJModbusHub,
        device_info,
        description: SajModbusSensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(platform_name=platform_name, hub=hub, device_info=device_info, description=description)

    def _same(self, dt1: datetime, dt2: datetime) -> bool:
        return dt1.date() == dt2.date()

class SajMonthSensor(SajDatetimeSensor):
    """Representation of a SAJ Modbus month sensor."""

    def __init__(
        self,
        platform_name: str,
        hub: SAJModbusHub,
        device_info,
        description: SajModbusSensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(platform_name=platform_name, hub=hub, device_info=device_info, description=description)

    def _same(self, dt1: datetime, dt2: datetime) -> bool:
        return dt1.month == dt2.month and dt1.year == dt2.year

class SajYearSensor(SajDatetimeSensor):
    """Representation of a SAJ Modbus year sensor."""

    def __init__(
        self,
        platform_name: str,
        hub: SAJModbusHub,
        device_info,
        description: SajModbusSensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(platform_name=platform_name, hub=hub, device_info=device_info, description=description)

    def _same(self, dt1: datetime, dt2: datetime) -> bool:
        return dt1.year == dt2.year
