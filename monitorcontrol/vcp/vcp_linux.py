from __future__ import annotations
from .vcp_codes import VPCCommand
from .vcp_abc import VCP, VCPIOError, VCPPermissionError
from types import TracebackType
from typing import List, Optional, Tuple, Type
import os
import struct
import sys
import time

from .vcp_codes import get_vcp_com

# hide the Linux code from Windows CI coverage
if sys.platform.startswith("linux"):
    import fcntl
    import pyudev


    class LinuxVCP(VCP):
        """
        Linux API access to a monitor's virtual control panel.

        References:
            https://github.com/Informatic/python-ddcci
            https://github.com/siemer/ddcci/
        """

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
            """
            Args:
                bus_number: I2C bus number.
            """
            super().__init__()
            self.bus_number = bus_number
            self.fd: Optional[str] = None
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
            except PermissionError as e:
                cleanup(self.fd)
                raise VCPPermissionError(f"permission error for {self.fp}") from e
            except OSError as e:
                cleanup(self.fd)
                raise VCPIOError(f"unable to open VCP at {self.fp}") from e
            except Exception as e:
                cleanup(self.fd)
                raise e
            return self

        def __exit__(
            self,
            exception_type: Optional[Type[BaseException]],
            exception_value: Optional[BaseException],
            exception_traceback: Optional[TracebackType],
        ) -> Optional[bool]:
            try:
                os.close(self.fd)
            except OSError as e:
                raise VCPIOError("unable to close descriptor") from e
            self.fd = None

            return super().__exit__(exception_type, exception_value, exception_traceback)

        def set_vcp_feature(self, code: VPCCommand, value: int):
            """
            Sets the value of a feature on the virtual control panel.

            Args:
                code: feature code
                value: feature value

            Raises:
                VCPIOError: failed to set VCP feature
            """

            assert self._in_ctx, "This function must be run within the context manager"
            if not code.writeable():
                raise TypeError(f"cannot write read-only code: {code.name}")
            elif code.readable() and code.discreet == False:
                maximum = self._get_code_maximum(code)
                if value > maximum:
                    raise ValueError(f"value of {value} exceeds code maximum of {maximum} for {code.name}")

            self.rate_limt()

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
            """
            Gets the value of a feature from the virtual control panel.

            Args:
                code: Feature code.

            Returns:
                Current feature value, maximum feature value.

            Raises:
                VCPIOError: Failed to get VCP feature.
            """

            assert self._in_ctx, "This function must be run within the context manager"
            if not code.readable():
                raise TypeError(f"cannot read write-only code: {code.name}")

            self.rate_limt()

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
                # else ignore

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

        def get_vcp_capabilities(self) -> dict:
            """
            Gets capabilities string from the virtual control panel.

            Returns:
                One long capabilities string in the format:
                "(prot(monitor)type(LCD)model(ACER VG271U)cmds(01 02 03 07 0C)"

                No error checking for the string being valid. String can have
                bit errors or dropped characters.

            Raises:
                VCPError: Failed to get VCP feature.
            """

            assert self._in_ctx, "This function must be run within the context manager"

            # Create an empty capabilities string to be filled with the data
            caps_str = ""

            self.rate_limt()

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
                    # else ignore
                # remove checksum from length

                # unpack the payload
                reply_code, payload = struct.unpack(f">B{length-1}s", payload)
                length -= 1

                if reply_code != self.GET_VCP_CAPS_REPLY:
                    raise VCPIOError(f"received unexpected response code: {reply_code}")

                # unpack the payload
                offset, payload = struct.unpack(f">H{length-2}s", payload)
                length -= 2

                if length > 0:
                    caps_str += payload.decode("ASCII")
                else:
                    break

                # update the offset and go again
                offset += length

            self.logger.debug(f"caps str={caps_str}")

            if loop_count >= loop_count_limit:
                raise VCPIOError("Capabilities string incomplete or too long")

            return _parse_capabilities(caps_str)

        @staticmethod
        def get_checksum(data: bytearray) -> int:
            """
            Computes the checksum for a set of data, with the option to
            use the virtual host address (per the DDC-CI specification).

            Args:
                data: Data array to transmit.

            Returns:
                Checksum for the data.
            """
            checksum = 0x00
            for data_byte in data:
                checksum ^= data_byte
            return checksum

        def rate_limt(self):
            """Rate limits messages to the VCP."""
            if self.last_set is None:
                return

            rate_delay = self.CMD_RATE - time.time() - self.last_set
            if rate_delay > 0:
                time.sleep(rate_delay)

        def read_bytes(self, num_bytes: int) -> bytes:
            """
            Reads bytes from the I2C bus.

            Args:
                num_bytes: number of bytes to read

            Raises:
                VCPIOError: unable to read data
            """
            try:
                return os.read(self.fd, num_bytes)
            except OSError as e:
                raise VCPIOError("unable to read from I2C bus") from e

        def write_bytes(self, data: bytes):
            """
            Writes bytes to the I2C bus.

            Args:
                data: data to write to the I2C bus

            Raises:
                VCPIOError: unable to write data
            """
            try:
                os.write(self.fd, data)
            except OSError as e:
                raise VCPIOError("unable write to I2C bus") from e


        @staticmethod
        def get_vcps() -> List[LinuxVCP]:
            """
            Interrogates I2C buses to determine if they are DDC-CI capable.

            Returns:
                List of all VCPs detected.
            """
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

    def _extract_a_cap(caps_str: str, key: str) -> str:
        """
        Splits the capabilities string into individual sets.

        Returns:
            Dict of all values for the capability
        """
        start_of_filter = caps_str.upper().find(key.upper())

        if start_of_filter == -1:
            # not all keys are returned by monitor.
            # Also, sometimes the string has errors.
            return ""

        start_of_filter += len(key)
        filtered_caps_str = caps_str[start_of_filter:]
        end_of_filter = 0
        for i in range(len(filtered_caps_str)):
            if filtered_caps_str[i] == "(":
                end_of_filter += 1
            if filtered_caps_str[i] == ")":
                end_of_filter -= 1
            if end_of_filter == 0:
                # don't change end_of_filter to remove the closing ")"
                break

        # 1:i to remove the first character "("
        return filtered_caps_str[1:i]

    def _convert_to_dict(caps_str: str) -> dict:
        """
        Parses the VCP capabilities string to a dictionary.
        Non-continuous capabilities will include an array of
        all supported values.

        Returns:
            Dict with all capabilities in hex

        Example:
            Expected string "04 14(05 06) 16" is converted to::

                {
                    0x04: {},
                    0x14: {0x05: {}, 0x06: {}},
                    0x16: {},
                }
        """

        if len(caps_str) == 0:
            # Sometimes the keys aren't found and the extracting of
            # capabilities returns an empty string.
            return {}

        result_dict = {}
        group = []
        prev_val = None
        for chunk in caps_str.replace("(", " ( ").replace(")", " ) ").split(" "):
            if chunk == "":
                continue
            elif chunk == "(":
                group.append(prev_val)
            elif chunk == ")":
                group.pop(-1)
            else:
                val = int(chunk, 16)
                if len(group) == 0:
                    result_dict[val] = {}
                else:
                    d = result_dict
                    for g in group:
                        d = d[g]
                    d[val] = {}
                prev_val = val

        return result_dict

    def _parse_capabilities(caps_str: str) -> dict:
        """
        Converts the capabilities string into a nice dict
        """
        caps_dict = {
            # Used to specify the protocol class
            "prot": "",
            # Identifies the type of display
            "type": "",
            # The display model number
            "model": "",
            # A list of supported VCP codes. Somehow not the same as "vcp"
            "cmds": "",
            # A list of supported VCP codes with a list of supported values
            # for each nc code
            "vcp": "",
            # undocumented
            "mswhql": "",
            # undocumented
            "asset_eep": "",
            # MCCS version implemented
            "mccs_ver": "",
            # Specifies the window, window type (PIP or Zone) safe area size
            # (bounded safe area) maximum size of the window, minimum size of
            # the window, and window supports VCP codes for control/adjustment.
            "window": "",
            # Alternate name to be used for control
            "vcpname": "",
            # Parsed input sources into text. Not part of capabilities string.
            "inputs": "",
            # Parsed color presets into text. Not part of capabilities string.
            "color_presets": "",
        }

        for key in caps_dict:
            if key in ["cmds", "vcp"]:
                caps_dict[key] = _convert_to_dict(_extract_a_cap(caps_str, key))
            else:
                caps_dict[key] = _extract_a_cap(caps_str, key)

        # Parse the input sources into a text list for readability
        input_source_cap = get_vcp_com("input_select").value
        if input_source_cap in caps_dict["vcp"]:
            caps_dict["inputs"] = []
            input_val_list = list(caps_dict["vcp"][input_source_cap].keys())
            input_val_list.sort()

            for val in input_val_list:
                input_source = val

                caps_dict["inputs"].append(input_source)

        # Parse the color presets into a text list for readability
        color_preset_cap = get_vcp_com("image_color_preset").value
        if color_preset_cap in caps_dict["vcp"]:
            caps_dict["color_presets"] = []
            color_val_list = list(caps_dict["vcp"][color_preset_cap])
            color_val_list.sort()

            for val in color_val_list:
                color_source = val

                caps_dict["color_presets"].append(color_source)

        return caps_dict