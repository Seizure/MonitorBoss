# MonitorBoss

Boss your monitors around. 👉🖥️🖥️🖥️

## Description
MonitorBoss makes use of the DDC/CI standard and MCCS protocol to communicate with monitors, allowing you to get information on their state and set applicable attributes. MonitorBoss currently only fully covers a subset of attributes supported by MCCS, though these are the most common ones.

### Supported Attributes
* Currently active input source
* Contrast
* Luminance/Brightness
* Power state
* Color mode
* Virtual Control Panel summary

## Requirements

### Environment
- Either Windows or Linux. Other systems are ***not*** supported at the moment, including macOS. 🙁
- Python version ??? is required to run source

### Dependencies

* [monitorcontrol](https://pypi.org/project/monitorcontrol/) - provides support for the MCCS protocol
* [PyInstaller](https://pypi.org/project/pyinstaller/) - for building application binaries

## Usage
```commandline
usage: monitorboss [-h] {list,get,set,tog} ...

Boss your monitors around.

options:
  -h, --help          show this help message and exit

subcommands:
  {list,get,set,tog}  basic commands
    list              list all the monitors and their possible attributes
    get               return the value of a given attribute
    set               sets a given attribute to a given value
    tog               toggles a given attribute between two given values
```

### list
```commandline
usage: monitorboss list [-h]

options:
  -h, --help  show this help message and exit
```

### get
```commandline
usage: monitorboss get [-h] attr mon

return the value of a given attribute

positional arguments:
  attr        the attribute to return
  mon         the monitor to control

options:
  -h, --help  show this help message and exit
```

### set
```commandline
usage: monitorboss set [-h] attr val mon [mon ...]

sets a given attribute to a given value

positional arguments:
  attr        the attribute to set
  val         the value to set the attribute to
  mon         the monitor(s) to control

options:
  -h, --help  show this help message and exit
```

### tog
```commandline
usage: monitorboss tog [-h] attr val1 val2 mon [mon ...]

toggles a given attribute between two given values

positional arguments:
  attr        the attribute to toggle
  val1        the first value to toggle between
  val2        the second value to toggle between
  mon         the monitor(s) to control

options:
  -h, --help  show this help message and exit
```

## Authors
* [@Rangi42](https://github.com/Rangi42)
* [@Seizure](https://github.com/Seizure)

## License
This project is licenced under LGPL v3.0. See [LICENSE.txt](LICENSE.txt) for more information.