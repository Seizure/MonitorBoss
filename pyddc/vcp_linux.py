# pragma: exclude file

from __future__ import annotations

from pyddc.vcp_codes import VCPCommand
from pyddc.vcp_abc import VCP, VCPIOError, VCPPermissionError, VCPFeatureReturn
from types import TracebackType
from typing import List, Optional, Type
import os
import struct
import sys
import time
import ctypes

assert sys.platform.startswith("linux"), "This file must be imported only for Linux"

import fcntl
import pyudev

GET_VCP_HEADER_LENGTH = 2  # header packet length
PROTOCOL_FLAG = 0x80  # protocol flag is bit 7 of the length byte

# VCP commands
GET_VCP_CMD = 0x01  # get VCP feature command
GET_VCP_REPLY = 0x02  # get VCP feature reply code
SET_VCP_CMD = 0x03  # set VCP feature command
GET_VCP_CAPS_CMD = 0xF3  # Capabilities Request command
GET_VCP_CAPS_REPLY = 0xE3  # Capabilities Request reply

# timeouts
CMD_RATE = 0.05  # at least 50ms between messages

# addresses
SEGMENT_ADDR = 0x30 # i2c segment address for EDIDs larger than 256 bytes
DDCCI_ADDR = 0x37  # DDC-CI command address on the I2C bus
EDID_I2C_ADDR = 0x50 # I2C slave address for EDID
HOST_ADDRESS = 0x51  # virtual I2C slave address of the host
I2C_SLAVE = 0x0703  # I2C bus slave address

# flags
I2C_M_RD = 0x0001  # read flag for I2C messages
I2C_RDWR = 0x0707  # I2C_RDWR ioctl transaction structure

class i2c_msg(ctypes.Structure):
    _fields_ = [
        ("addr", ctypes.c_uint16),
        ("flags", ctypes.c_uint16),
        ("len", ctypes.c_uint16),
        ("buf", ctypes.POINTER(ctypes.c_char)),
    ]

class i2c_rdwr_ioctl_data(ctypes.Structure):
    _fields_ = [
        ("msgs", ctypes.POINTER(i2c_msg)),
        ("nmsgs", ctypes.c_uint32),
    ]

GET_VCP_RESULT_CODES = {
    0: "No Error",
    1: "Unsupported VCP code",
}


# references:
# https://github.com/Informatic/python-ddcci
# https://github.com/siemer/ddcci/
class LinuxVCP(VCP):
    # TODO: maybe generalize this into general VCP functionality, as it will become relevant when we
    #  create macOS driver, and make Windows driver low level
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

        def cleanup():
            if self.fd is not None:
                try:
                    os.close(self.fd)
                except OSError:
                    pass

        try:
            self.fd = os.open(self.fp, os.O_RDWR)
            fcntl.ioctl(self.fd, I2C_SLAVE, DDCCI_ADDR)
            self.read_bytes(1)
        except PermissionError as err:
            cleanup()
            raise VCPPermissionError(f"permission error for {self.fp}") from err
        except OSError as err:
            cleanup()
            raise VCPIOError(f"unable to open VCP at {self.fp}") from err
        except Exception as err:
            cleanup()
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

    def _set_vcp_feature(self, com: VCPCommand, value: int, timeout: float):
        del timeout  # unused
        self.rate_limit()
        payload = bytearray()
        payload.append(SET_VCP_CMD)
        payload.append(com.code)
        low_byte, high_byte = struct.pack("<H", value)
        payload.append(high_byte)
        payload.append(low_byte)
        self._ddc_write(payload)
        self.last_set = time.time()

    def _get_vcp_feature(self, com: VCPCommand, timeout: float) -> VCPFeatureReturn:
        self.rate_limit()
        payload = bytearray()
        payload.append(GET_VCP_CMD)
        payload.append(com.code)
        self._ddc_write(payload)
        _, payload = self._ddc_read(timeout)
        # unpack the payload
        (
            reply_code,
            result_code,
            vcp_opcode,
            vcp_type_code,
            feature_max,
            feature_current,
        ) = struct.unpack(">BBBBHH", payload)
        if reply_code != GET_VCP_REPLY:
            raise VCPIOError(f"received unexpected response code: {reply_code}")
        if vcp_opcode != com.code:
            raise VCPIOError(f"received unexpected opcode: {vcp_opcode}")
        if result_code > 0:
            try:
                message = GET_VCP_RESULT_CODES[result_code]
            except KeyError:
                message = f"received result with unknown code: {result_code}"
            raise VCPIOError(message)
        return VCPFeatureReturn(feature_current, feature_max)

    def _get_vcp_capabilities_str(self, timeout: float) -> str:
        # Create an empty capabilities string to be filled with the data
        caps_str = ""
        self.rate_limit()
        offset = 0
        loop_count = 0
        loop_count_limit = 40
        while loop_count < loop_count_limit:
            loop_count += 1
            payload = bytearray()
            payload.append(GET_VCP_CAPS_CMD)
            low_byte, high_byte = struct.pack("<H", offset)
            payload.append(high_byte)
            payload.append(low_byte)
            self._ddc_write(payload)
            length, payload = self._ddc_read(timeout)
            # check if length is valid
            if length < 3 or length > 35:
                raise VCPIOError(f"received unexpected response length: {length}")
            # unpack reply code
            reply_code, payload = struct.unpack(f">B{length - 1}s", payload)
            length -= 1
            if reply_code != GET_VCP_CAPS_REPLY:
                raise VCPIOError(f"received unexpected response code: {reply_code}")
            # unpack offset and string data
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
            rate_delay = CMD_RATE - (time.time() - self.last_set)
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

    def _ddc_write(self, payload: bytearray):
        """Wrap payload in a DDC-CI packet (framing header + checksum) and write it to the bus."""
        data = bytearray(payload)
        data.insert(0, len(data) | PROTOCOL_FLAG)
        data.insert(0, HOST_ADDRESS)
        data.append(self.get_checksum(bytearray([DDCCI_ADDR << 1]) + data))
        self.logger.debug("data=" + " ".join([f"{x:02X}" for x in data]))
        self.write_bytes(data)

    def _ddc_read(self, timeout: float) -> tuple[int, bytes]:
        """Wait timeout seconds, read a DDC-CI response, validate its checksum.

        Returns a (length, payload) tuple where length is the data length from
        the response header (protocol flag cleared) and payload is the raw
        response payload bytes (checksum byte stripped).
        """
        time.sleep(timeout)
        header = self.read_bytes(GET_VCP_HEADER_LENGTH)
        self.logger.debug("header=" + " ".join([f"{x:02X}" for x in header]))
        _, length = struct.unpack("=BB", header)
        length &= ~PROTOCOL_FLAG  # clear protocol flag
        raw_payload = self.read_bytes(length + 1)
        self.logger.debug("payload=" + " ".join([f"{x:02X}" for x in raw_payload]))
        payload, checksum = struct.unpack(f"={length}sB", raw_payload)
        calculated_checksum = self.get_checksum(header + payload)
        checksum_xor = checksum ^ calculated_checksum
        if checksum_xor:
            message = f"checksum does not match: {checksum_xor}"
            if self.CHECKSUM_ERRORS.lower() == "strict":
                raise VCPIOError(message)
            elif self.CHECKSUM_ERRORS.lower() == "warning":
                self.logger.warning(message)
        return length, payload

    @staticmethod
    def _i2c_transaction(fd, addr, start_reg, length):
        """Standard Atomic Write-then-Read."""
        write_buf = ctypes.create_string_buffer(bytes([start_reg]))
        read_buf = ctypes.create_string_buffer(length)
        msgs = (i2c_msg * 2)(
            i2c_msg(addr=addr, flags=0, len=1, buf=write_buf),
            i2c_msg(addr=addr, flags=I2C_M_RD, len=length, buf=read_buf)
        )
        rdwr = i2c_rdwr_ioctl_data(msgs=msgs, nmsgs=2)
        fcntl.ioctl(fd, I2C_RDWR, rdwr)
        return read_buf.raw

    @staticmethod
    def _i2c_segmented_read(fd, segment_ptr, length):
        """
        Atomic Segmented Read:
        1. Write Segment Number to 0x30
        2. Write Offset 0 to 0x50
        3. Read N bytes from 0x50
        """
        # If segment is 0, we don't strictly need the segment pointer write,
        # but doing it anyway is more robust for some controllers.
        seg_buf = ctypes.create_string_buffer(bytes([segment_ptr]))
        off_buf = ctypes.create_string_buffer(bytes([0x00]))
        read_buf = ctypes.create_string_buffer(length)

        msgs = (i2c_msg * 3)(
            i2c_msg(addr=SEGMENT_ADDR, flags=0, len=1, buf=seg_buf),
            i2c_msg(addr=EDID_I2C_ADDR, flags=0, len=1, buf=off_buf),
            i2c_msg(addr=EDID_I2C_ADDR, flags=I2C_M_RD, len=length, buf=read_buf)
        )

        rdwr = i2c_rdwr_ioctl_data(msgs=msgs, nmsgs=3)
        fcntl.ioctl(fd, I2C_RDWR, rdwr)
        return read_buf.raw

    # TODO: there are two safety checks we probably want to implement:
    # 1. a cap on extensions. Some monitors will falsely report 255 extensions. 8 is a sane max for the real world
    # 2. run sanity checks on the EDID block header. The first block has a header of "00 FF FF FF FF FF FF". If this header
        # is detected in a following block, the monitor is looping and we can stop
    # 3. Each 128-byte block ends with a checksum byte. The sum of all bytes in a block must equal 0 (mod 256). If the
        # first block fails this test, its extension count is unreliable. If a follow up block fails this test, it is
        # either corrupt, or garbage data, and we can probably stop.
    def _get_edid_blob(self) -> bytes:
        device_path = f"/dev/i2c-{self.bus_number}"

        fd = os.open(device_path, os.O_RDWR)
        try:
            # 1. Atomic Discovery: Read first 128 bytes (Block 0)
            base_block = self._i2c_transaction(fd, EDID_I2C_ADDR, 0, 128)
            extension_count = base_block[126]

            if extension_count == 0:
                return base_block

            # 2. Determine how many 256-byte segments we need
            # Total blocks = Base (1) + Extensions (N)
            total_blocks = 1 + extension_count
            total_segments = (total_blocks + 1) // 2

            full_edid = bytearray()

            for segment in range(total_segments):
                # For each segment, read up to 2 blocks (256 bytes)
                blocks_in_this_segment = 2
                if segment == total_segments - 1 and total_blocks % 2 != 0:
                    blocks_in_this_segment = 1

                read_len = blocks_in_this_segment * 128

                # Atomic Segmented Read
                segment_data = self._i2c_segmented_read(fd, segment, read_len)
                full_edid.extend(segment_data)

            return bytes(full_edid)

        finally:
            os.close(fd)

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


if __name__ == "__main__":
    vcp_list = LinuxVCP.get_vcps()
    edids = {}
    for vcp in vcp_list:
        edids[str(vcp.bus_number)] = vcp._get_edid_blob()

    for bus, edid in edids.items():
        print(f"EDID for {bus}:\n{edid}")