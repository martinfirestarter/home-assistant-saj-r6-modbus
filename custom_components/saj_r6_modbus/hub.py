"""SAJ R6 Modbus Hub."""

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from voluptuous.validators import Number
import logging
import threading
from datetime import datetime, timedelta
from homeassistant.core import CALLBACK_TYPE, callback, HomeAssistant
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.helpers import entity_registry
from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusException
from pymodbus.pdu import ModbusPDU

from .const import (
    DEVICE_STATUSSES,
    FAULT_MESSAGES,
)

_LOGGER = logging.getLogger(__name__)

class SAJModbusHub(DataUpdateCoordinator[dict]):
    """Thread safe wrapper class for pymodbus."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        host: str,
        port: Number,
        scan_interval: Number,
    ):
        """Initialize the Modbus hub."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=timedelta(seconds=scan_interval),
        )

        self._client = ModbusTcpClient(host=host, port=port, timeout=5)
        self._lock = threading.Lock()

        self.inverter_data: dict = {}
        self.data: dict = {}

    @callback
    def async_remove_listener(self, update_callback: CALLBACK_TYPE) -> None:
        """Remove data update listener."""
        super().async_remove_listener(update_callback)

        """No listeners left then close connection"""
        if not self._listeners:
            self.close()

    def close(self) -> None:
        """Disconnect client."""
        with self._lock:
            self._client.close()

    def _read_holding_registers(self, unit, address, count):
        """Read holding registers."""
        with self._lock:
            return self._client.read_holding_registers(
                address=address, count=count, slave=unit
            )

    def convert_to_signed16(self, value):
        """Convert unsigned 16 bit integers to signed integers."""
        if value >= 0x8000:
            return value - 0x10000
        else:
            return value

    def convert_to_signed32(self, value):
        """Convert unsigned 32 bit integers to signed integers."""
        if value >= 0x80000000:
            return value - 0x100000000
        else:
            return value

    def parse_datetime (self, registers: list[int]) -> datetime:
        """Extract date and time values from registers."""

        year = registers[0]  # yyyy
        month = registers[1] >> 8  # MM
        day = registers[1] & 0xFF  # dd
        hour = registers[2] >> 8  # HH
        minute = registers[2] & 0xFF  # mm
        second = registers[3] >> 8  # ss

        timevalues = f"{year:04}{month:02}{day:02}{hour:02}{minute:02}{second:02}"
        # Convert to datetime object
        date_time_obj = datetime.astimezone(datetime.strptime(timevalues, '%Y%m%d%H%M%S'))

        return(date_time_obj)

    async def _async_update_data(self) -> dict:
        realtime_data = {}
        try:
            """Read inverter info"""
            self.inverter_data = await self.hass.async_add_executor_job(
                self.read_modbus_inverter_data
            )
            """Read realtime data"""
            realtime_data = await self.hass.async_add_executor_job(
                self.read_modbus_r6_realtime_data
            )

        except (BrokenPipeError, ConnectionResetError, ConnectionException) as conerr:
            _LOGGER.error("Reading realtime data failed! Inverter is unreachable.")
            _LOGGER.debug("Connection error: %s", conerr)

        self.close()
        return {**realtime_data}

    def read_modbus_inverter_data(self) -> dict:
        """Read data about inverter."""
        inverter_data = self._read_holding_registers(unit=1, address=0x8F00, count=29)

        if inverter_data.isError() or len(inverter_data.registers) != 29:
            return {}

        registers = inverter_data.registers
        data = {
            "type": registers[0],
            "subtype": round(registers[1] * 0.001, 3),
            "commproversion": round(registers[2] * 0.001, 3),
            "sn": ''.join(chr(registers[i] >> 8) + chr(registers[i] & 0xFF) for i in range(3, 13)).rstrip('\x00') if registers[3] != 0x00 else STATE_UNAVAILABLE,
            "pc": ''.join(chr(registers[i] >> 8) + chr(registers[i] & 0xFF) for i in range(13, 23)).rstrip('\x00') if registers[13] != 0x00 else STATE_UNAVAILABLE,
            "dv": f"{round(registers[23] * 0.001, 3):.3f}" if registers[23] != 0xFFFF else STATE_UNAVAILABLE,
            "mcv": f"{round(registers[24] * 0.001, 3):.3f}" if registers[24] != 0xFFFF else STATE_UNAVAILABLE,
            "scv": f"{round(registers[25] * 0.001, 3):.3f}" if registers[25] != 0xFFFF else STATE_UNAVAILABLE,
            "disphwversion": f"{round(registers[26] * 0.001, 3):.3f}" if registers[26] != 0xFFFF else STATE_UNAVAILABLE,
            "ctrlhwversion": f"{round(registers[27] * 0.001, 3):.3f}" if registers[27] != 0xFFFF else STATE_UNAVAILABLE,
            "powerhwversion": f"{round(registers[28] * 0.001, 3):.3f}" if registers[28] != 0xFFFF else STATE_UNAVAILABLE,
        }

        return data

    def read_modbus_r6_realtime_data(self) -> dict:
        """Read realtime data from inverter."""
        realtime_data = self._read_holding_registers(unit=1, address=0x6000, count=99)

        if realtime_data.isError() or len(realtime_data.registers) != 99:
            return {}

        registers = realtime_data.registers
        data = {}

        data["time"] = self.parse_datetime(registers[0:4])
        data["totalenergy"] = round((registers[4] << 16 | registers[5]) * 0.01, 2)
        data["yearenergy"] = round((registers[6] << 16 | registers[7]) * 0.01, 2)
        data["monthenergy"] = round((registers[8] << 16 | registers[9]) * 0.01, 2)
        data["todayenergy"] = round((registers[10] << 16 | registers[11]) * 0.01, 2)
        data["totalhour"] = round((registers[12] << 16 | registers[13]) * 0.1, 1)
        data["todayhour"] = round(registers[14] * 0.1, 1)

        data["errorcount"] = registers[15]
        data["errorsn"] = registers[16]
        data["settingdatasn"] = registers[17]
        # data["reserved"] = registers[18]
        mpvmode = registers[19]
        data["mpvmode"] = STATE_UNAVAILABLE if mpvmode < 1 or mpvmode > 3 else DEVICE_STATUSSES.get(mpvmode)
        faultMsg0 = registers[20] << 16 | registers[21]
        faultMsg1 = registers[22] << 16 | registers[23]
        faultMsg2 = registers[24] << 16 | registers[25]
        faultMsg = []
        faultMsg.extend(
            self.translate_fault_code_to_messages(faultMsg0, FAULT_MESSAGES[0].items())
        )
        faultMsg.extend(
            self.translate_fault_code_to_messages(faultMsg1, FAULT_MESSAGES[1].items())
        )
        faultMsg.extend(
            self.translate_fault_code_to_messages(faultMsg2, FAULT_MESSAGES[2].items())
        )
        # status value can hold max 255 chars in HA
        data["faultmsg"] = ", ".join(faultMsg).strip()[0:254]
        if faultMsg:
            _LOGGER.error("Fault message: " + ", ".join(faultMsg).strip())
        data["conntime"] = registers[26]

        data["energy"] = round((registers[27] << 16 | registers[28]) * 0.01, 2)
        data["power"] = (registers[29] << 16 | registers[30])
        data["qpower"] = self.convert_to_signed32((registers[31] << 16 | registers[32]))
        data["pf"] = round(self.convert_to_signed16(registers[33]) * 0.001, 3)

        data["l1volt"] = round(registers[34] * 0.1, 1)
        data["l1curr"] = round(registers[35] * 0.01, 2)
        data["l1freq"] = round(registers[36] * 0.01, 2)
        data["l1dci"] = self.convert_to_signed16(registers[37])
        data["l1power"] = registers[38]
        data["l1pf"] = round(self.convert_to_signed16(registers[39]) * 0.001, 3)
        data["l2volt"] = round(registers[40] * 0.1, 1)
        data["l2curr"] = round(registers[41] * 0.01, 2)
        data["l2freq"] = round(registers[42] * 0.01, 2)
        data["l2dci"] = self.convert_to_signed16(registers[43])
        data["l2power"] = registers[44]
        data["l2pf"] = round(self.convert_to_signed16(registers[45]) * 0.001, 3)
        data["l3volt"] = round(registers[46] * 0.1, 1)
        data["l3curr"] = round(registers[47] * 0.01, 2)
        data["l3freq"] = round(registers[48] * 0.01, 2)
        data["l3dci"] = self.convert_to_signed16(registers[49])
        data["l3power"] = registers[50]
        data["l3pf"] = round(self.convert_to_signed16(registers[51]) * 0.001, 3)
        data["nevolt"] = round(registers[52] * 0.1, 1)
        data["gfci"] = self.convert_to_signed16(registers[53])
        data["busvolt"] = round(registers[54] * 0.1, 1)
        data["busvoltm"] = round(registers[55] * 0.1, 1)

        data["invtempc1"] = round(self.convert_to_signed16(registers[56]) * 0.1, 1)
        data["invtempcl1"] = round(self.convert_to_signed16(registers[57]) * 0.1, 1)
        data["invtempcl2"] = round(self.convert_to_signed16(registers[58]) * 0.1, 1)
        data["invtempcl3"] = round(self.convert_to_signed16(registers[59]) * 0.1, 1)
        data["invtempccavity"] = round(self.convert_to_signed16(registers[60]) * 0.1, 1)
        # data["pvtempc1"] = round(self.convert_to_signed16(registers[61]) * 0.1, 1)
        # data["pvtempc2"] = round(self.convert_to_signed16(registers[62]) * 0.1, 1)
        # data["pvtempc3"] = round(self.convert_to_signed16(registers[63]) * 0.1, 1)
        # data["pvtempc4"] = round(self.convert_to_signed16(registers[64]) * 0.1, 1)

        data["iso1"] = registers[65]
        data["iso2"] = registers[66]
        data["iso3"] = registers[67]
        data["iso4"] = registers[68]

        data["pv1volt"] = round(registers[69] * 0.1, 1) if registers[69] != 0xFFFF else STATE_UNAVAILABLE
        data["pv1curr"] = round(registers[70] * 0.01, 2) if registers[70] != 0xFFFF else STATE_UNAVAILABLE
        data["pv1power"] = registers[71] if registers[71] != 0xFFFF else STATE_UNAVAILABLE
        data["pv2volt"] = round(registers[72] * 0.1, 1) if registers[72] != 0xFFFF else STATE_UNAVAILABLE
        data["pv2curr"] = round(registers[73] * 0.01, 2) if registers[73] != 0xFFFF else STATE_UNAVAILABLE
        data["pv2power"] = registers[74] if registers[74] != 0xFFFF else STATE_UNAVAILABLE
        data["pv3volt"] = round(registers[75] * 0.1, 1) if registers[75] != 0xFFFF else STATE_UNAVAILABLE
        data["pv3curr"] = round(registers[76] * 0.01, 2) if registers[76] != 0xFFFF else STATE_UNAVAILABLE
        data["pv3power"] = registers[77] if registers[77] != 0xFFFF else STATE_UNAVAILABLE
        data["pv4volt"] = round(registers[78] * 0.1, 1) if registers[78] != 0xFFFF else STATE_UNAVAILABLE
        data["pv4curr"] = round(registers[79] * 0.01, 2) if registers[79] != 0xFFFF else STATE_UNAVAILABLE
        data["pv4power"] = registers[80] if registers[80] != 0xFFFF else STATE_UNAVAILABLE
        data["pv5volt"] = round(registers[81] * 0.1, 1) if registers[81] != 0xFFFF else STATE_UNAVAILABLE
        data["pv5curr"] = round(registers[82] * 0.01, 2) if registers[82] != 0xFFFF else STATE_UNAVAILABLE
        data["pv5power"] = registers[83] if registers[83] != 0xFFFF else STATE_UNAVAILABLE
        data["pv6volt"] = round(registers[84] * 0.1, 1) if registers[84] != 0xFFFF else STATE_UNAVAILABLE
        data["pv6curr"] = round(registers[85] * 0.01, 2) if registers[85] != 0xFFFF else STATE_UNAVAILABLE
        data["pv6power"] = registers[86] if registers[86] != 0xFFFF else STATE_UNAVAILABLE
        data["pv1strcurr1"] = round(registers[87] * 0.01, 2) if registers[87] != 0xFFFF else STATE_UNAVAILABLE
        data["pv1strcurr2"] = round(registers[88] * 0.01, 2) if registers[88] != 0xFFFF else STATE_UNAVAILABLE
        data["pv2strcurr1"] = round(registers[89] * 0.01, 2) if registers[89] != 0xFFFF else STATE_UNAVAILABLE
        data["pv2strcurr2"] = round(registers[90] * 0.01, 2) if registers[90] != 0xFFFF else STATE_UNAVAILABLE
        data["pv3strcurr1"] = round(registers[91] * 0.01, 2) if registers[91] != 0xFFFF else STATE_UNAVAILABLE
        data["pv3strcurr2"] = round(registers[92] * 0.01, 2) if registers[92] != 0xFFFF else STATE_UNAVAILABLE
        data["pv4strcurr1"] = round(registers[93] * 0.01, 2) if registers[93] != 0xFFFF else STATE_UNAVAILABLE
        data["pv4strcurr2"] = round(registers[94] * 0.01, 2) if registers[94] != 0xFFFF else STATE_UNAVAILABLE
        data["pv5strcurr1"] = round(registers[95] * 0.01, 2) if registers[95] != 0xFFFF else STATE_UNAVAILABLE
        data["pv5strcurr2"] = round(registers[96] * 0.01, 2) if registers[96] != 0xFFFF else STATE_UNAVAILABLE
        data["pv6strcurr1"] = round(registers[97] * 0.01, 2) if registers[97] != 0xFFFF else STATE_UNAVAILABLE
        data["pv6strcurr2"] = round(registers[98] * 0.01, 2) if registers[98] != 0xFFFF else STATE_UNAVAILABLE

        return data

    def translate_fault_code_to_messages(
        self, fault_code: int, fault_messages: list
    ) -> list:
        """Translate faultcodes to readable messages."""
        messages = []
        if not fault_code:
            return messages

        for code, mesg in fault_messages:
            if fault_code & code:
                messages.append(mesg)

        return messages

