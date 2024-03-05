# Usage

```
usage: scratch.py [-h] {list,get,set,tog} ...

Boss your monitors around.

options:
  -h, --help          show this help message and exit

monitor commands:
  {list,get,set,tog}  commands for manipulating and polling your monitors
    list              list all the monitors and their possible attributes
    get               return the value of a given attribute
    set               sets a given attribute to a given value
    tog               toggles a given attribute between two given values
```

## list
```
usage: scratch.py list [-h]

list all the monitors and their possible attributes

options:
  -h, --help  show this help message and exit
```

## get
```
usage: scratch.py get [-h] attr mon

return the value of a given attribute

positional arguments:
  attr        the attribute to return
  mon         the monitor to control

options:
  -h, --help  show this help message and exit
```

## set
```
usage: scratch.py set [-h] attr val mon [mon ...]

sets a given attribute to a given value

positional arguments:
  attr        the attribute to set
  val         the value to set the attribute to
  mon         the monitor(s) to control

options:
  -h, --help  show this help message and exit
```

## tog
```
usage: scratch.py tog [-h] attr val1 val2 mon [mon ...]

toggles a given attribute between two given values

positional arguments:
  attr        the attribute to toggle
  val1        the first value to toggle between
  val2        the second value to toggle between
  mon         the monitor(s) to control

options:
  -h, --help  show this help message and exit
```

## Available attributes
* src - (currently active) input source
  * Must be a valid source ID, or alias as defined by the application built-ins or config file additions
* cnt - contrast
  * Must be an integer, though valid values will be constrained between 0 - 100 on most monitors
* lum - luminance/brightness
  * Must be an integer, though valid values will be constrained between 0 - 100 on most monitors
* pwr - power mode/state
  * Must be a valid power state, as defined by built-in aliases
* clr - (currently active) color preset
  * Must be a valid color temperature preset, as defined by built-in aliases
* vcp - summary of the Virtual Control Panel's abilities
  * This attribute can only be read
