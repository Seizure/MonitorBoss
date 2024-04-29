from collections import namedtuple
from dataclasses import dataclass

import objc
import Foundation
import Quartz

#######
# get list of displays
#######
error, display_ids_tuple, display_count = Quartz.CGGetOnlineDisplayList(16, None, None)
if error:
    raise OSError(f"Could not get display list. Error: {error}")

# print([x for x in dir(objc) if str(x).__contains__("_C_")])

IOKit = Foundation.NSBundle.bundleWithIdentifier_('com.apple.framework.IOKit')
IOKIT_functions = [("IORegistryGetRootEntry", b"II"),
                   ("IOObjectRelease", b"iI"),
                   ("IORegistryEntryCreateIterator", b"iI*I^I", '', {'arguments': {3: {'type_modifier': b'o'}}}),
                   ("IOIteratorNext", b"II"),
                   ("IORegistryEntryGetName", b"iI*", '',
                    {'arguments': {1: {'c_array_delimited_by_null': True, 'type_modifier': b'N'}}})]
objc.loadBundleFunctions(IOKit, globals(), IOKIT_functions)

# constants = [("KERN_SUCCESS", b"i"),
#                    ("kIOMasterPortDefault", b"i"),
#                    ("kIORegistryIterateRecursively", b"i")]
#
# objc.loadBundleVariables(IOKit, globals(), constants, skip_undefined=False)

# objc.loadBundleVariables could be used to load constants?? But I'm not sure which frameworks they are in
KERN_SUCCESS = 0  # IOKit constant
kIOMasterPortDefault = 0  # IOKit constant
kIORegistryIterateRecursively = 1  # IOKit constant
IO_OBJECT_NULL = 0  # IOKit constant
MACH_PORT_NULL = 0  # A constant, don't know what framework but probably IOKit?


@dataclass
class IOregService:
    edidUUID: str
    manufacturer: str
    productName: str
    serialNumber: int
    alphanumericSerialNumber: str
    location: str
    ioDisplayLocation: str
    transportUpstream: str
    transportDownstream: str
    # service: IOAVService
    serviceLocation: int
    displayAttributes: dict


@dataclass
class Arm64Service:
    strdisplayID: int
    # strservice: IOAVService
    strserviceLocation: int
    strdiscouraged: bool
    strdummy: bool
    strserviceDetails: IOregService
    strmatchScore: int


def ioregIterateToNextObjectOfInterest(interests: list[str], iterator: int) -> (str, int, int):
    entry = preceedingEntry = IO_OBJECT_NULL
    name = ""

    while True:
        preceedingEntry = entry
        entry = IOIteratorNext(iterator)
        if entry == MACH_PORT_NULL:
            break
        ret, name = IORegistryEntryGetName(entry, bytearray(128))
        name = name.decode()
        if ret != KERN_SUCCESS:
            break
        for interest in interests:
            if interest in name:
                ObjectOfInterest = namedtuple("ObjectOfInterest", ["name", "entry", "preceedingEntry"])
                objectOfInterest = ObjectOfInterest(name, entry, preceedingEntry)
                print(objectOfInterest)
                # return objectOfInterest

    return None


#####
# get list of IOregService, for matching displays against
#####
def getIoregServicesForMatching():
    serviceLocation = 0
    ioregServicesForMatching = []  # a list[IOregService]
    ioregRoot = IORegistryGetRootEntry(kIOMasterPortDefault)
    ioregService = IORegService()

    try:
        ret, iterator = IORegistryEntryCreateIterator(ioregRoot, "IOService".encode('utf-8'),
                                                      kIORegistryIterateRecursively, None)
        if ret != KERN_SUCCESS:
            return ioregServicesForMatching
        keyDCPAVServiceProxy = "DCPAVServiceProxy"
        keysFramebuffer = ["AppleCLCD2", "IOMobileFramebufferShim"]
        while True:
            objectOfInterest = ioregIterateToNextObjectOfInterest([keyDCPAVServiceProxy] + keysFramebuffer, iterator)
            if not objectOfInterest:
                break
            if objectOfInterest.name in keysFramebuffer:
                ##ioregService = self.getIORegServiceAppleCDC2Properties(objectOfInterest.entry)
                serviceLocation += 1
                ioregService.serviceLocation = serviceLocation
            elif objectOfInterest.name == keyDCPAVServiceProxy:
                ##self.setIORegServiceDCPAVServiceProxy(objectOfInterest.entry, ioregService) # ioregService should be a pointer to itself
                ioregServicesForMatching.append(ioregService)
        return ioregServicesForMatching
    finally:
        IOObjectRelease(ioregRoot)
        IOObjectRelease(iterator)


print(getIoregServicesForMatching())

#######
# try to get DDC services, and skip displays which error
######
display_ids = []
for d in display_ids_tuple:
    pass