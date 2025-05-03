import zlib
from lib.utils.constants import (DOWNLOAD_OPERATION, STOP_AND_WAIT)


class InitSegment:
    def __init__(self, opcode=DOWNLOAD_OPERATION, protocol=STOP_AND_WAIT,
                 ack=0b0, name=b""):
        self.ack = ack & 0b1
        self.opcode = opcode & 0b1
        self.protocol = protocol & 0b1
        self.name = name

    def _build_header(self):
        return (self.ack << 2) | (self.opcode << 1) | self.protocol

    def serialize(self, verbose=False):
        if verbose:
            print(f"Serializing InitMessage: "
                  f"\n\t- ack: {self.ack}"
                  f"\n\t- opcode: {self.opcode}"
                  f"\n\t- protocol: {self.protocol}"
                  f"\n\t- name: {self.name}")

        header_byte = self._build_header()
        header_bytes = bytes([header_byte])

        name_bytes = self.name.encode("utf-8")
        name_length = len(name_bytes)
        name_length_byte = name_length.to_bytes(1, byteorder="big")

        packet_to_crc = header_bytes + name_length_byte + name_bytes
        crc = zlib.crc32(packet_to_crc) & 0xFFFFFFFF
        crc_bytes = crc.to_bytes(4, byteorder="big")

        final_packet = packet_to_crc + crc_bytes

        if verbose:
            print("[InitSegment] Header Byte:", bin(header_byte))
            print("[InitSegment] Name Length:", name_length)
            print("[InitSegment] CRC:", hex(crc))
            print("[InitSegment] Serialized Packet:", final_packet)

        return final_packet

    @staticmethod
    def deserialize(data, verbose=False) -> 'InitSegment':
        if len(data) < 6:
            raise ValueError("Packet too short")

        header_byte = data[0]
        name_length = data[1]

        if len(data) < (2 + name_length + 4):
            raise ValueError("Incomplete packet")

        file_name = data[2:2 + name_length]
        crc_received = int.from_bytes(data[2 + name_length:], byteorder="big")
        crc_calculated = zlib.crc32(data[:2 + name_length]) & 0xFFFFFFFF

        if crc_calculated != crc_received:
            raise ValueError("CRC mismatch")

        ack = (header_byte >> 2) & 0b1
        opcode = (header_byte >> 1) & 0b1
        protocol = header_byte & 0b1

        if verbose:
            print("Deserialize InitSegment result:")
            print("\t opcode:", opcode)
            print("\t protocol:", protocol)
            print("\t ack:", ack)
            print("\t name:", file_name)

        return InitSegment(opcode, protocol, ack, file_name)


class StopAndWaitSegment:
    def __init__(self, payload=b"", seq_num=0, ack_num=0,
                 eof_num=0):
        self.payload = payload
        self.seq_num = seq_num & 0b1
        self.ack_num = ack_num & 0b1
        self.eof_num = eof_num & 0b1

    def _build_header(self):
        return (self.seq_num << 2) | (self.ack_num << 1) | self.eof_num

    def serialize(self, verbose=True):
        header_byte = self._build_header()
        header_bytes = bytes([header_byte])
        payload_len_bytes = len(self.payload).to_bytes(2, byteorder="big")
        packet_to_crc = header_bytes + payload_len_bytes + self.payload
        crc = zlib.crc32(packet_to_crc) & 0xFFFFFFFF
        crc_bytes = crc.to_bytes(4, byteorder="big")

        final_packet = packet_to_crc + crc_bytes

        if verbose:
            print("[StopAndWait] Header Byte:", bin(header_byte))
            print("[StopAndWait] Payload Length:", len(self.payload))
            print("[StopAndWait] CRC:", hex(crc))
            print("[StopAndWait] Serialized Packet:", final_packet)

        return final_packet

    @staticmethod
    def deserialize(data) -> 'StopAndWaitSegment':
        if len(data) < 7:
            raise ValueError("Packet too short")

        header_byte = data[0]
        payload_len = int.from_bytes(data[1:3], byteorder="big")

        if len(data) < (3 + payload_len + 4):
            raise ValueError("Incomplete packet")

        payload = data[3:3 + payload_len]
        crc_received = int.from_bytes(data[3 + payload_len:3 +
                                           payload_len + 4], byteorder="big")
        crc_calculated = zlib.crc32(data[:3 + payload_len]) & 0xFFFFFFFF

        if crc_calculated != crc_received:
            raise ValueError("CRC mismatch")

        seq_num = (header_byte >> 2) & 0b1
        ack_num = (header_byte >> 1) & 0b1
        eof_num = header_byte & 0b1

        return StopAndWaitSegment(payload, seq_num, ack_num, eof_num)


class SelectiveRepeatSegment:
    def __init__(self, payload=b"", seq_num=0, ack_num=0,
                 win_size=0):
        self.payload = payload
        self.seq_num = seq_num & 0xFFFF
        self.ack_num = ack_num & 0xFFFF
        self.win_size = win_size & 0xFFFF

    def serialize(self, verbose=False):
        payload_len_bytes = len(self.payload).to_bytes(2, byteorder="big")
        seq_num_bytes = self.seq_num.to_bytes(2, byteorder="big")
        ack_num_bytes = self.ack_num.to_bytes(2, byteorder="big")
        win_size_bytes = self.win_size.to_bytes(2, byteorder="big")

        packet_to_crc = seq_num_bytes + ack_num_bytes \
            + win_size_bytes \
            + payload_len_bytes \
            + self.payload
        crc = zlib.crc32(packet_to_crc) & 0xFFFFFFFF
        crc_bytes = crc.to_bytes(4, byteorder="big")

        final_packet = packet_to_crc + crc_bytes

        if verbose:
            print("[SelectiveRepeat] Seq:", self.seq_num, " Ack:",
                  self.ack_num, " Win:", self.win_size)
            print("[SelectiveRepeat] Payload Length:", len(self.payload))
            print("[SelectiveRepeat] CRC:", hex(crc))
            print("[SelectiveRepeat] Serialized Packet:", final_packet)

        return final_packet

    @staticmethod
    def deserialize(data) -> 'SelectiveRepeatSegment':
        if len(data) < 12:
            raise ValueError("Packet too short")

        seq_num = int.from_bytes(data[0:2], byteorder="big")
        ack_num = int.from_bytes(data[2:4], byteorder="big")
        win_size = int.from_bytes(data[4:6], byteorder="big")
        payload_len = int.from_bytes(data[6:8], byteorder="big")

        if len(data) < (8 + payload_len + 4):
            raise ValueError("Incomplete packet")

        payload = data[8:8 + payload_len]
        crc_received = int.from_bytes(data[8 + payload_len:], byteorder="big")
        crc_calculated = zlib.crc32(data[:8 + payload_len]) & 0xFFFFFFFF

        if crc_calculated != crc_received:
            raise ValueError("CRC mismatch")

        return SelectiveRepeatSegment(payload, seq_num, ack_num, win_size)
