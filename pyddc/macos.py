from collections import namedtuple
from ctypes import Union
from dataclasses import dataclass
from PyObjCTools import Conversion
import time

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
                   ("IOAVServiceCreateWithService", b"@@I"),
                   ("IOAVServiceWriteI2C", b"i@II^[I]I"), # https://gist.github.com/alin23/531151c49e013554e6ca2186cef3fa90
                   ("IOAVServiceReadI2C", b"i@II^[I]I", '', # https://gist.github.com/alin23/531151c49e013554e6ca2186cef3fa90
                    {'arguments': {3: {'type_modifier': b'o', 'c_array_of_fixed_length': 12}}})]
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
ARM64_DDC_DATA_ADDRESS = 0x51 # defined in Arm64DDC.swift in MonitorControl project
ARM64_DDC_7BIT_ADDRESS = 0x37 # defined in Arm64DDC.swift in MonitorControl project


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
    service = None
    serviceLocation: int = None
    displayAttributes: dict = None

    def __str__(self):
        return f"< IORegservice: Model={self.productName}; Serial={self.serialNumber}; Location={self.location} >"


@dataclass
class Arm64Service:
    strdisplayID: int = None
    # strservice: IOAVService = None
    strserviceLocation: int = None
    strdiscouraged: bool = None
    strdummy: bool = None
    strserviceDetails: IOregService = None
    strmatchScore: int = None

def checksum(chk: int, data: [int], start: int, end: int) -> int:
    chkd = chk
    for i in range(start, end+1):
        chkd ^= data[i]
    return chkd



def performDDCCommunication(ioavservice, send: [int], writeSleepTime: float = 0.01, numOfWriteCycles: int = 2, readSleepTime: float = 0.05, numOfRetryAttempts: int = 4, retrySleepTime: int = 0) -> Union[int, None]
    assert ioavservice is not None, "Are you dumb?"

    dataAddress = ARM64_DDC_DATA_ADDRESS
    success = False
    reply = []

    packet = [0x80 | len(send)+1, len(send)]
    for snd in send:
        packet.append(snd)
    packet.append(0) # per comments in Arm64DDC.swift: the last byte is the place of the checksum, see next line!
    packet[-1] = checksum(ARM64_DDC_7BIT_ADDRESS << 1 if len(send) == 1 else ARM64_DDC_7BIT_ADDRESS << 1 ^ dataAddress, packet, 0, len(packet)-2)

    #here is where I changed things
    for _ in range(0, numOfRetryAttempts):
        time.sleep(writeSleepTime)
        success = IOAVServiceWriteI2C(ioavservice, ARM64_DDC_7BIT_ADDRESS, dataAddress, packet, len(packet)) == 0
        if success:
            time.sleep(readSleepTime)
            ret, rep = IOAVServiceReadI2C(ioavservice, ARM64_DDC_7BIT_ADDRESS, dataAddress, None, 12)
            if ret == 0:
                chksm = checksum(0x50, rep, 0, len(rep) - 2)
                if chksm == rep[-1]:
                    return rep
                reply = rep


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
            print(dir(ioavService))
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


services = getIoregServicesForMatching()
for s in services:
    print(s)

#######
# try to get DDC services, and skip displays which error
######
display_ids = []
for d in display_ids_tuple:
    pass