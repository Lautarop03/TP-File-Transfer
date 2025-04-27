import struct
import zlib


class StopAndWaitPacket:
    def __init__(self, payload=b"", seq_num=0, ack_nak=0, ack_num=0):
        self.payload = payload
        self.seq_num = seq_num & 0b1  # 1 bit
        self.ack_nak = ack_nak & 0b1  # 1 bit
        self.ack_num = ack_num & 0b1  # 1 bit

    def _build_header(self):
        # 5 bits padding (00000), 1 bit seq_num, 1 bit ack_nak, 1 bit ack_num
        return (self.seq_num << 2) | (self.ack_nak << 1) | self.ack_num

    def serialize(self):
        header_byte = self._build_header()

        # 1 header byte + payload length + payload data
        packet_wo_crc = (
            struct.pack("!B", header_byte)
            + struct.pack("!H", len(self.payload))
            + self.payload
        )

        # Calculate CRC32
        crc = zlib.crc32(packet_wo_crc) & 0xFFFFFFFF
        # return the serialized packet with the CRC at the end
        return packet_wo_crc + struct.pack("!I", crc)

    @staticmethod
    def deserialize(data):
        if len(data) < 7:
            raise ValueError("Packet too short")

        # Extract the header
        header_byte = data[0]

        payload_len = struct.unpack("!H", data[1:3])[0]

        payload = data[3 : 3 + payload_len]

        crc_received = struct.unpack("!I", data[3 + payload_len :])[0]

        # Check the CRC
        crc_calculated = zlib.crc32(data[:-4]) & 0xFFFFFFFF

        if crc_calculated != crc_received:
            raise ValueError("CRC mismatch")

        # Extract the header values
        seq_num = (header_byte >> 2) & 0b1
        ack_nak = (header_byte >> 1) & 0b1
        ack_num = header_byte & 0b1

        return StopAndWaitPacket(payload, seq_num, ack_nak, ack_num)
