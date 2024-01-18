# MonitorBoss

Boss your monitors around. 👉🖥️🖥️🖥️

## Description
MonitorBoss makes use of the DDC/CI standard and MCCS protocol to communicate with monitors, allowing you to get information on their state and set applicable attributes. MonitorBoss currently only fully covers a subset of attributes supported by MCCS, though these are the most common ones.

### Supported Attributes
* Currently active input source
* Contrast
* Luminance/Brightness
* Power state
* Color preset
* Virtual Control Panel summary

## Requirements

### OS
Either Windows or Linux. Other systems are ***not*** supported at the moment, including macOS. 🙁

### Source Dependencies

* [monitorcontrol](https://pypi.org/project/monitorcontrol/) - provides support for the MCCS protocol
* [PyInstaller](https://pypi.org/project/pyinstaller/) - for building application binaries
* Python version ???

## Usage
For help with running MonitorBoss in the command line, see [USAGE.md](USAGE.md)

## Authors
* [@Rangi42](https://github.com/Rangi42)
* [@Seizure](https://github.com/Seizure)

## License
This project is licenced under LGPL v3.0. See [LICENSE.txt](LICENSE.txt) for more information.