## SAJ R6 Inverter Modbus - A Home Assistant custom component for SAJ R6 inverters

Home Assistant Custom Component for reading data from SAJ R6 Inverters through Modbus TCP.

Implements SAJ R6 Inverter registers from [`saj-modbus-communication-protocol.pdf`](https://github.com/martinfirestarter/home-assistant-saj-r6-modbus/blob/main/saj-modbus-communication-protocol.pdf).

This integration has been tested with SAJ R6-15K-T2-32 inverter with SAJ AIO3 module.
The module exposes a Modbus TCP Server on port 502.

### Features

- Installation through Config Flow UI.
- Separate sensor per register
- Auto applies scaling factor
- Configurable polling interval
- All Modbus registers are read within 1 read cycle for data consistency between sensors.


## Installation

Add folder custom_components\saj_r6_modbus to your configuration.

### Configuration
Go to the Integrations page in your configuration and click on new Integration -> SAJ R6 Modbus.

Home Assistant Custom Component for reading data from SAJ R6 Inverters through Modbus over TCP.
This integration should work with SAJ R6 inverters.

##  Credits

Idea based on [`home-assistant-saj-r5-modbus`](https://github.com/wimb0/home-assistant-saj-r5-modbus) from [@wimb0](https://github.com/wimb0).
 
[![saj_logo](https://github.com/martinfirestarter/home-assistant-saj-r6-modbus/blob/main/images/saj_r6_modbus/logo.png)](https://www.saj-electric.com/)

<!-- References -->

[home-assistant]: https://www.home-assistant.io/
[release-url]: https://github.com/martinfirestarter/home-assistant-saj-r6-modbus/releases
