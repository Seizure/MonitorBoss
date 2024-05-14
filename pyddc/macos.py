import ctypes
from collections import namedtuple
from dataclasses import dataclass
from typing import Union
from PyObjCTools import Conversion
import time

import objc
import Foundation

read_buffer_size = 11  # have seen multiple decisions on this, what should it be?

# initial thread with argument metadata: https://stackoverflow.com/questions/51862518/calling-function-with-ctypes-or-pyobjc
IOKit = Foundation.NSBundle.bundleWithIdentifier_('com.apple.framework.IOKit')
IOKIT_functions = [("IORegistryGetRootEntry", b"II"),
                   ("IOObjectRelease", b"iI"),
                   ("IORegistryEntryCreateIterator", b"iI*I^I", '',
                    # this is technically a [c128] not a * but this works with less hoops. Should check back later to consider ramifications
                    {'arguments': {3: {'type_modifier': b'o'}}}),
                   ("IOIteratorNext", b"II"),
                   ("IORegistryEntryGetName", b"iI[128c]", '',
                    {'arguments': {1: {'c_array_delimited_by_null': True, 'type_modifier': b'N'}}}),
                   ("IORegistryEntryCreateCFProperty", b"@I@@I"),
                   ("IORegistryEntryGetPath", b"iI*[512c]"),
                   # this is technically a [c128] not a * but this works with less hoops. Should check back later to consider ramifications
                   ("IOAVServiceCreateWithService", b"@@I"),
                   ("IOAVServiceWriteI2C", b"i@II^[I]I", '',
                    {'arguments': {3: {'type_modifier': b'n', 'c_array_length_in_arg': 4}}}),
                   # https://gist.github.com/alin23/531151c49e013554e6ca2186cef3fa90
                   ("IOAVServiceReadI2C", b"i@II^[I]I", '',
                    # https://gist.github.com/alin23/531151c49e013554e6ca2186cef3fa90
                    {'arguments': {3: {'type_modifier': b'o', 'c_array_of_fixed_length': read_buffer_size}}})]
objc.loadBundleFunctions(IOKit, globals(), IOKIT_functions)

KERN_SUCCESS = 0  # IOKit constant
kIOMasterPortDefault = 0  # IOKit constant
kIORegistryIterateRecursively = 1  # IOKit constant
IO_OBJECT_NULL = 0  # IOKit constant
MACH_PORT_NULL = 0  # A constant, don't know what framework but probably IOKit?
kCFAllocatorDefault = None  # NULL. A constant from Core Foundation
kIOServicePlane = "IOService"  # IOKit constant
ARM64_DDC_DATA_ADDRESS = 0x51  # defined in Arm64DDC.swift in MonitorControl project
ARM64_DDC_7BIT_ADDRESS = 0x37  # defined in Arm64DDC.swift in MonitorControl project


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
    for i in range(start, end + 1):
        chkd ^= data[i]
    return chkd


def read(ioavservice,
         command: int,
         writeSleepTime: float = 0.01,
         numOfWriteCycles: int = 2,
         readSleepTime: float = 0.05,
         numOfRetryAttempts: int = 4,
         retrySleepTime: int = 0) -> Union[tuple[int, int], None]:
    send = [command]

    success, reply = performDDCCommunication(ioavservice, send, True, writeSleepTime, numOfWriteCycles, readSleepTime,
                                         numOfRetryAttempts, retrySleepTime)
    # print('reply', (success, list(reply)))
    if success:
        val_max = reply[6] * 256 + reply[7]
        val_cur = reply[8] * 256 + reply[9]
        return val_cur, val_max
    else:
        return None


def performDDCCommunication(ioavservice, send: [int], read_reply: bool, writeSleepTime: float = 0.01,
                            numOfWriteCycles: int = 2,
                            readSleepTime: float = 0.05, numOfRetryAttempts: int = 4, retrySleepTime: float = 0.01) \
        -> (bool, list[int]):
    assert ioavservice is not None, "Are you dumb?"

    success = False
    packet = bytearray()
    packet.append(0x80 | (len(send) + 1))
    packet.append(len(send))
    for snd in send:
        packet.append(snd)
    packet.append(0)  # per comments in Arm64DDC.swift: the last byte is the place of the checksum, see next line!
    packet[-1] = checksum(ARM64_DDC_7BIT_ADDRESS << 1 if len(send) == 1 else ARM64_DDC_7BIT_ADDRESS << 1 ^ dataAddress,
                          packet, 0, len(packet) - 2)

    # print(f"packet to send: {list(packet)}")

    rep = []
    for _ in range(0, numOfRetryAttempts):
        # why do we have multiple, default of 2, write cycles? Do we need this?
        for _ in range(0, max(numOfWriteCycles, 1)):
            time.sleep(writeSleepTime)
            success = IOAVServiceWriteI2C(ioavservice, ARM64_DDC_7BIT_ADDRESS, ARM64_DDC_DATA_ADDRESS, packet, len(packet)) == 0
        rep = []
        if read_reply:
            time.sleep(readSleepTime)
            ret, rep = IOAVServiceReadI2C(ioavservice, ARM64_DDC_7BIT_ADDRESS, ARM64_DDC_DATA_ADDRESS, None, read_buffer_size)
            if ret == 0:
                success = checksum(0x50, rep, 0, len(rep) - 2) == rep[-1]
        if success:
            return success, rep
        time.sleep(retrySleepTime)

    return success, rep


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

    NSDictDisplayAttrs = IORegistryEntryCreateCFProperty(entry, "DisplayAttributes", kCFAllocatorDefault,
                                                         kIORegistryIterateRecursively)
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

    NSDictTransport = IORegistryEntryCreateCFProperty(entry, "Transport", kCFAllocatorDefault,
                                                      kIORegistryIterateRecursively)
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
            # print(ioavService)
            # print(type(ioavService))
            # print(dir(ioavService))
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


features = {'contrast': 18, 'luminance': 16, 'input': 96}
displays = getIoregServicesForMatching()
ddc_displays = [d for d in displays if d.service is not None]

for d in ddc_displays:
    print(f"{d}:")
    for f in features:
        result = read(d.service, features[f], 0.05, 10)
        print(f"\tFeature <{f}>: {result}")