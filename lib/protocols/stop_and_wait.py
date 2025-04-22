import socket
from utils.file_manager import FileManager
from utils.constants import TIMEOUT, BUFFER_SIZE, WRITE_MODE, READ_MODE, MAX_ATTEMPTS
import struct


class Packet:
    # Clase packet provisional para testear funcionamiento localmente
    def __init__(self, data=b"", seq_num=0, ack=0):
        self.seq_num = seq_num  # 0 o 1
        self.data = data  # bytes
        self.ack = ack  # 0 o 1

    def serialize(self):
        data_length = len(self.data)
        header = struct.pack(
            "!B B I", self.seq_num, self.ack, data_length
        )  # !B B I: 1 byte para seq, 1 byte para ack, 4 bytes para longitud
        return header + self.data  # Empaquetamos el header y los datos binarios (data)

    @staticmethod
    def deserialize(bytes_data):
        # Desempaquetamos el header
        header = bytes_data[:6]  # Los primeros 6 bytes contienen el header
        seq_num, ack, data_length = struct.unpack("!B B I", header)

        # El resto es el data, basado en la longitud que hemos desempaquetado
        data = bytes_data[6 : 6 + data_length]

        return Packet(data, seq_num, ack)


# Custom exceptions for the Stop and Wait protocol
# TODO: Ubicarlas en su lugar
class MaxSendAttemptsExceeded(Exception):
    pass


class PacketDuplicateOrCorrupted(Exception):
    pass


class StopAndWait:
    def __init__(self, socket, ip, port):
        self.ip = ip
        self.port = port

        self.ack = 0  # ACK 0 o 1
        self.seq = 0  # Packet 0 o 1
        self.socket = socket
        self.send_attempts = 0

    def send(self, data):  # Send a single package

        packet = Packet(data=data, seq_num=self.seq)

        serialized_packet = packet.serialize()

        while MAX_ATTEMPTS > self.send_attempts:

            self.socket.sendto(serialized_packet, (self.ip, self.port))

            # Wait for ACK
            # Set the timeout for receiving the ACK
            self.socket.settimeout(TIMEOUT)
            try:
                ack_packet, _ = self.socket.recvfrom(
                    BUFFER_SIZE
                )
                ack_packet = Packet.deserialize(ack_packet)

                if ack_packet.ack == self.seq:
                    # Package received successfully
                    self.seq = 1 - self.seq
                    self.send_attempts = 0
                    return  
                else:
                    # The ACK is not what I expect
                    print(f"[CLIENT] Duplicate or corrupt package: {ack_packet}") # Debug
                    

            except socket.timeout:
                print(
                    f"[CLIENT] Timeout waiting for ACK"
                ) # Debug

            self.send_attempts += 1

        # exited the while, the packet could not be sent -> the program closes
        raise MaxSendAttemptsExceeded(
            f"The packet with seq {self.seq} could not be sent after {MAX_ATTEMPTS} attempts."
        )

    def receive(self):  # Receive a single package
        serialized_packet, address = self.socket.recvfrom(BUFFER_SIZE)
        packet = Packet.deserialize(serialized_packet)

        if packet.seq_num == self.ack:
            # Expected packet
            # Send ACK
            ack_packet = Packet(ack=self.ack)
            serialized_ack = ack_packet.serialize()
            self.socket.sendto(serialized_ack, address)

            self.ack = 1 - self.ack

            return packet.data
        else:
            # Duplicate or out-of-order packet
            print(f"[SERVER] Duplicate or corrupt package: {packet}")

            # send the last ACK I received
            ack_packet = Packet(ack=self.ack)
            serialized_ack = ack_packet.serialize()
            self.socket.sendto(serialized_ack, address)

            raise PacketDuplicateOrCorrupted(
                f"Expected: {self.ack}, Received: {packet.seq_num}"
            )

    def send_file(self, file_path):
        file_manager = FileManager(file_path, READ_MODE)
        file_manager.open()
        file_size = file_manager.file_size()

        while file_size > 0:
            data = file_manager.read()
            self.send(data)
            file_size -= len(data)

        file_manager.close()

        # TODO: Cambiar como se manda el EOF, cuando esten los MSG
        self.send(b"EOF")

    def receive_file(self, path):
        file_manager = FileManager(path, WRITE_MODE)
        file_manager.open()

        while True:
            try:
                data = self.receive()

                # TODO: Cambiar como se recibe el EOF, cuando esten los MSG
                if data == b"EOF":
                    print("[SERVER] End of file received.")  # Debug
                    break

                # Escribir al archivo
                file_manager.write(data)
            except PacketDuplicateOrCorrupted:
                continue
            except Exception as e:
                print(f"[SERVER] Error receiving: {e}")  # Debug
                break

        file_manager.close()
        print("[SERVER] File saved successfully.")  # Debug
