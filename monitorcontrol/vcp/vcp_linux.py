from __future__ import annotations
from .vcp_codes import VPCCommand
from .vcp_abc import VCP, VCPIOError, VCPPermissionError
from types import TracebackType
from typing import List, Optional, Tuple, Type
import os
import struct
import sys
import time

assert sys.platform.startswith("linux"), "This file must be imported only for Linux"

import fcntl
import pyudev


# references:
# https://github.com/Informatic/python-ddcci
# https://github.com/siemer/ddcci/
class LinuxVCP(VCP):
    GET_VCP_HEADER_LENGTH = 2  # header packet length
    PROTOCOL_FLAG = 0x80  # protocol flag is bit 7 of the length byte

    # VCP commands
    GET_VCP_CMD = 0x01  # get VCP feature command
    GET_VCP_REPLY = 0x02  # get VCP feature reply code
    SET_VCP_CMD = 0x03  # set VCP feature command
    GET_VCP_CAPS_CMD = 0xF3  # Capabilities Request command
    GET_VCP_CAPS_REPLY = 0xE3  # Capabilities Request reply

    # timeouts
    GET_VCP_TIMEOUT = 0.04  # at least 40ms per the DDCCI specification
    CMD_RATE = 0.05  # at least 50ms between messages

    # addresses
    DDCCI_ADDR = 0x37  # DDC-CI command address on the I2C bus
    HOST_ADDRESS = 0x51  # virtual I2C slave address of the host
    I2C_SLAVE = 0x0703  # I2C bus slave address

    GET_VCP_RESULT_CODES = {
        0: "No Error",
        1: "Unsupported VCP code",
    }

    CHECKSUM_ERRORS: str = "ignore"

    def __init__(self, bus_number: int):
        super().__init__()
        self.bus_number = bus_number
        self.fd: Optional[int] = None
        self.fp: str = f"/dev/i2c-{self.bus_number}"
        # time of last feature set call
        self.last_set: Optional[float] = None

    def __enter__(self):
        super().__enter__()

        def cleanup(fd: Optional[int]):
            if fd is not None:
                try:
                    os.close(self.fd)
                except OSError:
                    pass

        try:
            self.fd = os.open(self.fp, os.O_RDWR)
            fcntl.ioctl(self.fd, self.I2C_SLAVE, self.DDCCI_ADDR)
            self.read_bytes(1)
        except PermissionError as err:
            cleanup(self.fd)
            raise VCPPermissionError(f"permission error for {self.fp}") from err
        except OSError as err:
            cleanup(self.fd)
            raise VCPIOError(f"unable to open VCP at {self.fp}") from err
        except Exception as err:
            cleanup(self.fd)
            raise err
        return self

    def __exit__(
            self,
            exception_type: Optional[Type[BaseException]],
            exception_value: Optional[BaseException],
            exception_traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        try:
            os.close(self.fd)
        except OSError as err:
            raise VCPIOError("unable to close descriptor") from err
        self.fd = None
        return super().__exit__(exception_type, exception_value, exception_traceback)

    def set_vcp_feature(self, code: VPCCommand, value: int):
        self.rate_limit()
        # transmission data
        data = bytearray()
        data.append(self.SET_VCP_CMD)
        data.append(code.value)
        low_byte, high_byte = struct.pack("H", value)
        data.append(high_byte)
        data.append(low_byte)
        # add headers and footers
        data.insert(0, (len(data) | self.PROTOCOL_FLAG))
        data.insert(0, self.HOST_ADDRESS)
        data.append(self.get_checksum(bytearray([self.DDCCI_ADDR << 1]) + data))
        # write data
        self.logger.debug("data=" + " ".join([f"{x:02X}" for x in data]))
        self.write_bytes(data)
        # store time of last set VCP
        self.last_set = time.time()

    def get_vcp_feature(self, code: VPCCommand) -> Tuple[int, int]:
        self.rate_limit()
        # transmission data
        data = bytearray()
        data.append(self.GET_VCP_CMD)
        data.append(code.value)
        # add headers and footers
        data.insert(0, (len(data) | self.PROTOCOL_FLAG))
        data.insert(0, self.HOST_ADDRESS)
        data.append(self.get_checksum(bytearray([self.DDCCI_ADDR << 1]) + data))
        # write data
        self.logger.debug("data=" + " ".join([f"{x:02X}" for x in data]))
        self.write_bytes(data)
        # wait
        time.sleep(self.GET_VCP_TIMEOUT)
        # read the data
        header = self.read_bytes(self.GET_VCP_HEADER_LENGTH)
        self.logger.debug("header=" + " ".join([f"{x:02X}" for x in header]))
        source, length = struct.unpack("=BB", header)
        length &= ~self.PROTOCOL_FLAG  # clear protocol flag
        payload = self.read_bytes(length + 1)
        self.logger.debug("payload=" + " ".join([f"{x:02X}" for x in payload]))
        # check checksum
        payload, checksum = struct.unpack(f"={length}sB", payload)
        calculated_checksum = self.get_checksum(header + payload)
        checksum_xor = checksum ^ calculated_checksum
        if checksum_xor:
            message = f"checksum does not match: {checksum_xor}"
            if self.CHECKSUM_ERRORS.lower() == "strict":
                raise VCPIOError(message)
            elif self.CHECKSUM_ERRORS.lower() == "warning":
                self.logger.warning(message)
        # unpack the payload
        (
            reply_code,
            result_code,
            vcp_opcode,
            vcp_type_code,
            feature_max,
            feature_current,
        ) = struct.unpack(">BBBBHH", payload)
        if reply_code != self.GET_VCP_REPLY:
            raise VCPIOError(f"received unexpected response code: {reply_code}")
        if vcp_opcode != code.value:
            raise VCPIOError(f"received unexpected opcode: {vcp_opcode}")
        if result_code > 0:
            try:
                message = self.GET_VCP_RESULT_CODES[result_code]
            except KeyError:
                message = f"received result with unknown code: {result_code}"
            raise VCPIOError(message)
        return feature_current, feature_max

    def _get_vcp_capabilities_str(self) -> str:
        # Create an empty capabilities string to be filled with the data
        caps_str = ""
        self.rate_limit()
        # Get the first 32B of capabilities string
        offset = 0
        # Keep a count going to keep things sane
        loop_count = 0
        loop_count_limit = 40
        while loop_count < loop_count_limit:
            loop_count += 1
            # transmission data
            data = bytearray()
            data.append(self.GET_VCP_CAPS_CMD)
            low_byte, high_byte = struct.pack("H", offset)
            data.append(high_byte)
            data.append(low_byte)
            # add headers and footers
            data.insert(0, (len(data) | self.PROTOCOL_FLAG))
            data.insert(0, self.HOST_ADDRESS)
            data.append(self.get_checksum(data))
            # write data
            self.write_bytes(data)
            # wait
            time.sleep(self.GET_VCP_TIMEOUT)
            # read the data
            header = self.read_bytes(self.GET_VCP_HEADER_LENGTH)
            self.logger.debug("header=" + " ".join([f"{x:02X}" for x in header]))
            source, length = struct.unpack("BB", header)
            length &= ~self.PROTOCOL_FLAG  # clear protocol flag
            payload = self.read_bytes(length + 1)
            self.logger.debug("payload=" + " ".join([f"{x:02X}" for x in payload]))
            # check if length is valid
            if length < 3 or length > 35:
                raise VCPIOError(f"received unexpected response length: {length}")
            # check checksum
            payload, checksum = struct.unpack(f"{length}sB", payload)
            calculated_checksum = self.get_checksum(header + payload)
            checksum_xor = checksum ^ calculated_checksum
            if checksum_xor:
                message = f"checksum does not match: {checksum_xor}"
                if self.CHECKSUM_ERRORS.lower() == "strict":
                    raise VCPIOError(message)
                elif self.CHECKSUM_ERRORS.lower() == "warning":
                    self.logger.warning(message)
            # unpack the payload
            reply_code, payload = struct.unpack(f">B{length - 1}s", payload)
            length -= 1
            if reply_code != self.GET_VCP_CAPS_REPLY:
                raise VCPIOError(f"received unexpected response code: {reply_code}")
            # unpack the payload
            offset, payload = struct.unpack(f">H{length - 2}s", payload)
            length -= 2
            if length > 0:
                caps_str += payload.decode("ascii")
            else:
                break
            # update the offset and go again
            offset += length
        self.logger.debug(f"caps str={caps_str}")
        if loop_count >= loop_count_limit:
            raise VCPIOError("Capabilities string incomplete or too long")
        return caps_str

    @staticmethod
    def get_checksum(data: bytearray) -> int:
        checksum = 0x00
        for data_byte in data:
            checksum ^= data_byte
        return checksum

    def rate_limit(self):
        if self.last_set is not None:
            rate_delay = self.CMD_RATE - time.time() - self.last_set
            if rate_delay > 0:
                time.sleep(rate_delay)

    def read_bytes(self, num_bytes: int) -> bytes:
        try:
            return os.read(self.fd, num_bytes)
        except OSError as err:
            raise VCPIOError("unable to read from I2C bus") from err

    def write_bytes(self, data: bytes):
        try:
            os.write(self.fd, data)
        except OSError as err:
            raise VCPIOError("unable write to I2C bus") from err

    @staticmethod
    def get_vcps() -> List[LinuxVCP]:
        vcps = []
        # iterate I2C devices
        for device in pyudev.Context().list_devices(subsystem="i2c"):
            vcp = LinuxVCP(device.sys_number)
            try:
                with vcp:
                    pass
            except (OSError, VCPIOError):
                pass
            else:
                vcps.append(vcp)
        return vcps
