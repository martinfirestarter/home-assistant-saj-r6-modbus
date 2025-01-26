## SAJ R6 Inverter Modbus - A Home Assistant custom component for SAJ R6 inverters

Home assistant Custom Component for reading data from SAJ R6 inverters through Modbus TCP.

Implements SAJ Inverter registers from [`saj-modbus-communicationprotocol.pdf`](https://github.com/martinfirestarter/home-assistant-saj-r6-modbus/blob/main/saj-modbus-communicationprotocol.pdf).


### Features

- Installation through Config Flow UI.
- Separate sensor per register
- Auto applies scaling factor
- Configurable polling interval
- All Modbus registers are read within 1 read cycle for data consistency between sensors.


### Configuration
Go to the integrations page in your configuration and click on new integration -> SAJ R6 Modbus

Home Assistant Custom Component for reading data from SAJ R6 inverters through Modbus TCP.
This integration should work with SAJ R6 inverters.

## Installation

TBD


##  Credits

 Idea based on [`home-assistant-saj-r5-modbus`](https://github.com/wimb0/home-assistant-saj-r5-modbus) from [@wimb0](https://github.com/wimb0).
 
[![saj_logo](https://github.com/martinfirestarter/home-assistant-saj-r6-modbus/blob/main/images/saj_modbus/logo.png)](https://www.saj-electric.com/)
