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
        # TODO: 2 bytes para len no es mucho?
        packet_to_crc = header_bytes + payload_len_bytes + self.payload

        # Calculate CRC32
        crc = zlib.crc32(packet_to_crc) & 0xFFFFFFFF
        crc_bytes = crc.to_bytes(4, byteorder="big") # 4 bytes
    
        return packet_to_crc + crc_bytes

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

class InitSegment:
    def __init__(self, opcode=0, protocol=0, file_name=b"", file_path=b""):
        self.opcode = opcode & 0b1
        self.protocol = protocol & 0b1
        self.file_name = file_name
        self.file_path = file_path

    def _build_header(self):
        # 6 bits padding (000000), 1 bit opcode, 1 bit protocol
        return (self.opcode << 1) | self.protocol
    
    def serialize(self):
        header_byte = self._build_header()
        
        header_bytes = bytes([header_byte])

        file_name_len_bytes = len(self.file_name).to_bytes(1, byteorder="big")

        file_path_len_bytes = len(self.file_path).to_bytes(1, byteorder="big")

        packet_to_crc = header_bytes + file_name_len_bytes + self.file_name + file_path_len_bytes + self.file_path

        # Calculate CRC32
        crc = zlib.crc32(packet_to_crc) & 0xFFFFFFFF
        crc_bytes = crc.to_bytes(4, byteorder="big") # 4 bytes
    
        return packet_to_crc + crc_bytes
    
    @staticmethod
    def deserialize(data):
        if len(data) < 7:
            raise ValueError("Packet too short")

        # Extract the header
        header_byte = data[0]
        file_name_len = data[1]
        file_path_len = data[2 + file_name_len]

        if len(data) < (3 + file_name_len + file_path_len + 4):
            raise ValueError("Incomplete packet")

        file_name = data[2:2 + file_name_len]
        file_path = data[3 + file_name_len:3 + file_name_len + file_path_len]
        crc_received = int.from_bytes(data[3 + file_name_len + file_path_len:], byteorder="big")

        # Check the CRC
        crc_calculated = zlib.crc32(data[:3 + file_name_len + file_path_len]) & 0xFFFFFFFF
        if crc_calculated != crc_received:
            raise ValueError("CRC mismatch")

        # Extract the header values
        opcode = (header_byte >> 1) & 0b1
        protocol = header_byte & 0b1

        return InitSegment(opcode, protocol, file_name, file_path)