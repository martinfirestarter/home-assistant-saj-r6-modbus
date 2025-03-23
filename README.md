[![release][release-badge]][release-url]
![active][active-badge]
![downloads][downloads-badge]
[![hacs][hacs-badge]][hacs-url]
![license][lic-badge]


<a href="https://buymeacoffee.com/wimbo" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/white_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>

## SAJ R6 Inverter Modbus - A Home Assistant custom component for SAJ R6 inverters

Home assistant Custom Component for reading data from SAJ R6 Inverters through modbus TCP.

Implements SAJ R6 Inverter registers from [`saj-modbus-communication-protocol.pdf`](https://github.com/martinfirestarter/home-assistant-saj-r6-modbus/blob/main/saj-modbus-communication-protocol.pdf).


### Features

- Installation through Config Flow UI.
- Separate sensor per register
- Auto applies scaling factor
- Configurable polling interval
- All modbus registers are read within 1 read cycle for data consistency between sensors.


### Configuration
Go to the integrations page in your configuration and click on new integration -> SAJ R6 Modbus

Home Assistant Custom Component for reading data from SAJ R6 Inverters through modbus over TCP.
This integration should work with SAJ R6 inverters.

## Installation

ToDo

##  Credits

 Idea based on [`home-assistant-saj-r5-modbus`](https://github.com/wimb0/home-assistant-saj-r5-modbus) from [@wimb0](https://github.com/wimb0).
 
[![saj_logo](https://github.com/martinfirestarter/home-assistant-saj-r6-modbus/blob/main/images/saj_r6_modbus/logo.png)](https://www.saj-electric.com/)

<!-- References -->

[home-assistant]: https://www.home-assistant.io/
[release-url]: https://github.com/martinfirestarter/home-assistant-saj-r6-modbus/releases
