import zlib


class StopAndWaitSegment:
    def __init__(self, payload=b"", seq_num=0, ack_num=0):
        self.payload = payload
        self.seq_num = seq_num & 0b1  # 1 bit
        self.ack_num = ack_num & 0b1  # 1 bit

    def _build_header(self):
        # 6 bits padding (000000), 1 bit seq_num, 1 bit ack_num
        return (self.seq_num << 1) | self.ack_num

    def serialize(self):
        header_byte = self._build_header()
        
        header_bytes = bytes([header_byte])  # 1 byte
        payload_len_bytes = len(self.payload).to_bytes(2, byteorder="big")  # 2 bytes

        packet_wo_crc = header_bytes + payload_len_bytes + self.payload

        # Calculate CRC32
        crc = zlib.crc32(packet_wo_crc) & 0xFFFFFFFF
        crc_bytes = crc.to_bytes(4, byteorder="big") # 4 bytes
    
        return packet_wo_crc + crc_bytes

    @staticmethod
    def deserialize(data):
        if len(data) < 7:
            raise ValueError("Packet too short")

        # Extract the header
        header_byte = data[0]
        payload_len = int.from_bytes(data[1:3], byteorder="big")

        if len(data) < (3 + payload_len + 4):
            raise ValueError("Incomplete packet")

        payload = data[3:3 + payload_len]
        crc_received = int.from_bytes(data[3 + payload_len:3 + payload_len + 4], byteorder="big")

        # Check the CRC
        crc_calculated = zlib.crc32(data[:3 + payload_len]) & 0xFFFFFFFF
        if crc_calculated != crc_received:
            raise ValueError("CRC mismatch")

        # Extract the header values
        seq_num = (header_byte >> 1) & 0b1
        ack_num = header_byte & 0b1

        return StopAndWaitSegment(payload, seq_num, ack_num)
