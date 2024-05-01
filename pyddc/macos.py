from collections import namedtuple
from dataclasses import dataclass
from PyObjCTools import Conversion

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
                   ("IORegistryEntryCreateIterator", b"iI*I^I", '', # this is technically a [c128] not a * but this works with less hoops. Should check back later to consider ramifications
                    {'arguments': {3: {'type_modifier': b'o'}}}),
                   ("IOIteratorNext", b"II"),
                   ("IORegistryEntryGetName", b"iI[128c]", '',
                    {'arguments': {1: {'c_array_delimited_by_null': True, 'type_modifier': b'N'}}}),
                   ("IORegistryEntryCreateCFProperty", b"@I@@I"),
                   ("IORegistryEntryGetPath", b"iI*[512c]"), # this is technically a [c128] not a * but this works with less hoops. Should check back later to consider ramifications
                   ("IOAVServiceCreateWithService", b"@@I")]
objc.loadBundleFunctions(IOKit, globals(), IOKIT_functions)

# constants = [("KERN_SUCCESS", b"i"),
#                    ("kIOMasterPortDefault", b"i"),
#                    ("kIORegistryIterateRecursively", b"i")]
#
# objc.loadBundleVariables(IOKit, globals(), constants, skip_undefined=False)

# objc.loadBundleVariables could be used to load constants?? But doesn't seem to be working
KERN_SUCCESS = 0  # IOKit constant
kIOMasterPortDefault = 0  # IOKit constant
kIORegistryIterateRecursively = 1  # IOKit constant
IO_OBJECT_NULL = 0  # IOKit constant
MACH_PORT_NULL = 0  # A constant, don't know what framework but probably IOKit?
kCFAllocatorDefault = None  # NULL. A constant from Core Foundation
kIOServicePlane = "IOService"  # IOKit constant


@dataclass
class IOregService:
    edidUUID: str = None
    manufacturerID: str = None
    productName: str = None
    serialNumber: int = None
    alphanumericSerialNumber: str = None
    location: str = None
    ioDisplayLocation: str = None
    transportUpstream: str = None
    transportDownstream: str = None
    # service: IOAVService = None
    serviceLocation: int = None
    displayAttributes: dict = None


@dataclass
class Arm64Service:
    strdisplayID: int = None
    # strservice: IOAVService = None
    strserviceLocation: int = None
    strdiscouraged: bool = None
    strdummy: bool = None
    strserviceDetails: IOregService = None
    strmatchScore: int = None


def getIORegServiceAppleCDC2Properties(entry: int) -> IOregService:
    ioregService = IOregService()

    # I'm getting None back for edidUUID on the first use. Need to make sure that's expected
    edidUUID = IORegistryEntryCreateCFProperty(entry, "EDID UUID", kCFAllocatorDefault, kIORegistryIterateRecursively)
    if edidUUID:
        # print(f"edidUUID: {edidUUID}")
        ioregService.edidUUID = edidUUID

    cpath = bytearray(512)
    IORegistryEntryGetPath(entry, kIOServicePlane.encode("utf-8"), cpath)
    cpath = cpath.decode().rstrip('\0')
    # print(f"cpath: {cpath}")
    ioregService.ioDisplayLocation = cpath

    NSDictDisplayAttrs = IORegistryEntryCreateCFProperty(entry, "DisplayAttributes", kCFAllocatorDefault, kIORegistryIterateRecursively)
    # print(f"NSDictDisplayAttrs: {NSDictDisplayAttrs}")
    # print(f"NSDictDisplayAttrs class: {NSDictDisplayAttrs.__class__}")
    if NSDictDisplayAttrs:
        displayAttrs = Conversion.pythonCollectionFromPropertyList(NSDictDisplayAttrs)
        ioregService.displayAttributes = displayAttrs
        if "ProductAttributes" in displayAttrs:
            productAttributes = displayAttrs["ProductAttributes"]
            ioregService.manufacturerID = productAttributes.get("ManufacturerID")
            ioregService.productName = productAttributes.get("ProductName")
            ioregService.serialNumber = productAttributes.get("SerialNumber")
            ioregService.alphanumericSerialNumber = productAttributes.get("AlphanumericSerialNumber")
            # print(productAttributes)
            # print(type(productAttributes))

    NSDictTransport = IORegistryEntryCreateCFProperty(entry, "Transport", kCFAllocatorDefault, kIORegistryIterateRecursively)
    if NSDictTransport:
        transport = Conversion.pythonCollectionFromPropertyList(NSDictTransport)
        ioregService.transportUpstream = transport.get("Upstream")
        ioregService.transportDownstream = transport.get("Downstream")

    return ioregService


def setIORegServiceDCPAVServiceProxy(entry: int, ioregService: IOregService):
    location = IORegistryEntryCreateCFProperty(entry, "Location", kCFAllocatorDefault, kIORegistryIterateRecursively)
    if location:
        ioregService.location = location
        if location == "External":
            ioavService = IOAVServiceCreateWithService(kCFAllocatorDefault, entry)
            print(ioavService)
            print(type(ioavService))
            ioregService.service = ioavService


def ioregIterateToNextObjectOfInterest(interests: list[str], iterator: int) -> (str, int, int):
    entry = IO_OBJECT_NULL

    while True:
        preceedingEntry = entry
        entry = IOIteratorNext(iterator)
        if entry == MACH_PORT_NULL:
            break
        ret, name = IORegistryEntryGetName(entry, bytearray(128))
        if ret != KERN_SUCCESS:
            break
        name = name.decode()
        for interest in interests:
            if interest in name:
                ObjectOfInterest = namedtuple("ObjectOfInterest", ["name", "entry", "preceedingEntry"])
                objectOfInterest = ObjectOfInterest(name, entry, preceedingEntry)
                # print(objectOfInterest)
                return objectOfInterest

    return None


#####
# get list of IOregService, for matching displays against
#####
def getIoregServicesForMatching() -> list[IOregService]:
    serviceLocation = 0
    ioregServicesForMatching = []  # a list[IOregService]
    ioregRoot = IORegistryGetRootEntry(kIOMasterPortDefault)
    ioregService: IOregService

    try:
        ret, iterator = IORegistryEntryCreateIterator(ioregRoot, "IOService".encode('utf-8'),
                                                      kIORegistryIterateRecursively, None)
        if ret != KERN_SUCCESS:
            return ioregServicesForMatching
        keyDCPAVServiceProxy = "DCPAVServiceProxy"
        keysFramebuffer = ["AppleCLCD2", "IOMobileFramebufferShim"]
        ioregService = IOregService()
        while True:
            objectOfInterest = ioregIterateToNextObjectOfInterest([keyDCPAVServiceProxy] + keysFramebuffer, iterator)
            if not objectOfInterest:
                break
            if objectOfInterest.name in keysFramebuffer:
                ioregService = getIORegServiceAppleCDC2Properties(objectOfInterest.entry)
                serviceLocation += 1
                ioregService.serviceLocation = serviceLocation
            elif objectOfInterest.name == keyDCPAVServiceProxy:
                setIORegServiceDCPAVServiceProxy(objectOfInterest.entry, ioregService)
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