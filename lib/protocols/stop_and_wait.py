import socket
from lib.utils.file_manager import FileManager
from lib.utils.constants import (
    TIMEOUT, BUFFER_SIZE, WRITE_MODE, READ_MODE, MAX_ATTEMPTS)
from lib.utils.segments import StopAndWaitSegment
from lib.exceptions import MaxSendAttemptsExceeded, PacketDuplicateOrCorrupted


class StopAndWait:
    def __init__(self, socket, ip, port):
        self.ip = ip
        self.port = port

        self.ack = 0  # ACK 0 o 1
        self.seq = 0  # Packet 0 o 1
        self.socket = socket
        self.send_attempts = 0

    def send(self, payload, eof=0):  # Send a single package
        packet = StopAndWaitSegment(
            payload=payload, seq_num=self.seq, eof_num=eof)
        serialized_packet = packet.serialize()

        while MAX_ATTEMPTS > self.send_attempts:
            self.socket.sendto(serialized_packet, (self.ip, self.port))

            # Wait for ACK
            # Set the timeout for receiving the ACK
            self.socket.settimeout(TIMEOUT)
            try:
                ack_packet, _ = self.socket.recvfrom(BUFFER_SIZE)
                ack_packet = StopAndWaitSegment.deserialize(ack_packet)

                if ack_packet.ack_num == self.seq:
                    # Package received successfully
                    self.seq = 1 - self.seq
                    self.send_attempts = 0
                    return
                else:
                    # The ACK is not what I expect
                    print(
                        f"[CLIENT] Duplicate or corrupt package: {ack_packet}"
                    )  # Debug

            except socket.timeout:
                print("[CLIENT] Timeout waiting for ACK")  # Debug

            self.send_attempts += 1

        # exited the while, the packet could not be sent -> the program closes
        raise MaxSendAttemptsExceeded(
            f"The packet with seq {self.seq} could not be sent"
            f" after {MAX_ATTEMPTS} attempts."
        )

    def receive(self):  # Receive a single package
        serialized_packet, address = self.socket.recvfrom(BUFFER_SIZE)
        packet = StopAndWaitSegment.deserialize(serialized_packet)

        if packet.seq_num == self.ack:
            # Expected packet
            # Send ACK
            ack_packet = StopAndWaitSegment(ack_num=self.ack)
            serialized_ack = ack_packet.serialize()
            self.socket.sendto(serialized_ack, address)
            self.ack = 1 - self.ack

            return packet
        else:
            # Duplicate or out-of-order packet
            print(f"[SERVER] Duplicate or corrupt package: {packet}")

            # send the last ACK I received
            ack_packet = StopAndWaitSegment(ack_num=1 - self.ack)
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

        self.send(b"", eof=1)  # Send EOF

    def receive_file(self, path):
        file_manager = FileManager(path, WRITE_MODE)
        file_manager.open()

        while True:
            try:
                data = self.receive()

                if data.eof_num == 1:
                    print("[SERVER] EOF received.")
                    break

                # Write the file
                file_manager.write(data.payload)
            except PacketDuplicateOrCorrupted:
                continue
            except Exception as e:
                print(f"[SERVER] Error receiving: {e}")  # Debug
                break

        file_manager.close()
        print("[SERVER] File saved successfully.")  # Debug
