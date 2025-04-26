import os
import socket
from typing import Tuple
import zlib
from connection_info import ConnectionInfo
from protocols.stop_and_wait import StopAndWait
# TODO: Import when implemented
# from protocols.selective_repeat import SelectiveRepeat


class InitMessageParser:
    @staticmethod
    def parse(data: bytes, server_socket: socket.socket,
              client_address: Tuple[str, int], verbose: bool = False
              ) -> Tuple[bool, ConnectionInfo]:
        """
        Parse INIT message and return success flag and connection info
        Message structure:
        - Opcode (1B): 1 for download, 2 for upload
        - Protocol (1B): 1 for Stop & Wait, 2 for Selective Repeat
        - Path Length p (1B)
        - File Name (p B) - Used in Upload only
        - Path Length q (1B)
        - Path (q B) - Used in Download only
        - CRC32 Checksum (4B)
        """
        try:
            # Check minimum message size (1B + 1B + 1B + 4B = 7 bytes minimum)
            if len(data) < 7:
                raise ValueError("Message too short")

            # Extract header fields
            opcode = data[0]
            protocol = data[1]
            path_length_p = data[2]

            current_pos = 3

            # Validate opcode
            if opcode not in [1, 2]:  # 1: Download, 2: Upload
                raise ValueError(f"Invalid opcode: {opcode}")

            # Validate protocol
            if protocol not in [1, 2]:  # 1: SW, 2: SR
                raise ValueError(f"Invalid protocol: {protocol}")

            protocol_str = "sw" if protocol == 1 else "sr"
            is_download = (opcode == 1)

            # Parse paths based on operation type
            if is_download:
                # Skip filename field (not used in download)
                current_pos += path_length_p
                if current_pos >= len(data) - 5:
                    # -5 for path_length_q and CRC32
                    raise ValueError("Message truncated in download path")

                path_length_q = data[current_pos]
                current_pos += 1

                if current_pos + path_length_q + 4 > len(data):
                    raise ValueError("Message truncated in download path")

                file_path = data[current_pos:current_pos +
                                 path_length_q].decode('utf-8')
                current_pos += path_length_q

                # Validate that the file exists for download
                if not os.path.exists(file_path):
                    raise ValueError(f"Download file not found: {file_path}")

            else:  # Upload
                if current_pos + path_length_p + 4 > len(data):
                    raise ValueError("Message truncated in upload filename")

                file_path = data[current_pos:current_pos +
                                 path_length_p].decode('utf-8')
                current_pos += path_length_p

                # Skip path field (not used in upload)
                path_length_q = data[current_pos]
                current_pos += path_length_q + 1

            # Verify CRC32
            expected_crc = int.from_bytes(data[-4:], byteorder='big')
            actual_crc = zlib.crc32(data[:-4]) & 0xFFFFFFFF

            if expected_crc != actual_crc:
                raise ValueError(
                    f"CRC32 mismatch. Expected: {expected_crc},"
                    f" Got: {actual_crc}")

            if verbose:
                print("Valid INIT message received:")
                print(f"Operation: {'Download' if is_download else 'Upload'}")
                print(f"Protocol: {protocol_str}")
                print(f"File path: {file_path}")

            # Create appropriate protocol handler
            if protocol_str == "sw":
                protocol_handler = StopAndWait(
                    server_socket, client_address[0], client_address[1])
            else:
                # TODO: Implement SelectiveRepeat handler
                protocol_handler = None

            return True, ConnectionInfo(
                is_download=is_download,
                protocol=protocol_str,
                file_path=file_path,
                protocol_handler=protocol_handler
            )

        except Exception as e:
            return False, str(e)

    @staticmethod
    def create_init_message(config) -> bytes:
        """
        Create INIT message according to protocol specification
        Message structure:
        - Opcode (1B): 1 for download, 2 for upload
        - Protocol (1B): 1 for Stop & Wait, 2 for Selective Repeat
        - Path Length p (1B)
        - File Name (p B) - Used in Upload only
        - Path Length q (1B)
        - Path (q B) - Used in Download only
        - CRC32 Checksum (4B)
        """
        # Prepare header fields
        opcode = 1 if config.is_download else 2
        protocol = 1 if config.protocol == "sw" else 2

        # Prepare file paths
        if config.is_download:
            filename = b""
            path = config.file_path.encode('utf-8')
        else:
            filename = config.file_path.encode('utf-8')
            path = b""

        # Construct message
        message = bytearray([
            opcode,
            protocol,
            len(filename),  # p
        ])
        message.extend(filename)
        message.append(len(path))  # q
        message.extend(path)

        # Add CRC32
        crc = zlib.crc32(message) & 0xFFFFFFFF
        message.extend(crc.to_bytes(4, byteorder='big'))

        return bytes(message)
