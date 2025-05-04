from queue import Queue, Empty
from lib.utils.constants import (
    TIMEOUT, MAX_ATTEMPTS)
from lib.utils.segments import StopAndWaitSegment
from lib.exceptions import MaxSendAttemptsExceeded


class StopAndWait:
    def __init__(self, socket, address, verbose, quiet):
        self.destination_address = address

        self.ack = 0  # ACK 0 o 1
        self.seq = 0  # Packet 0 o 1
        self.socket = socket
        self.send_attempts = 0
        self.verbose = verbose
        self.quiet = quiet
        self.ack_queue = Queue()  # Queue for receiving ACKs

    def send(self, payload, eof=0, expect_ack=True):  # Send a single package
        sw_segment = StopAndWaitSegment(
            payload=payload, seq_num=self.seq, eof_num=eof)

        serialized_packet = sw_segment.serialize()

        while MAX_ATTEMPTS > self.send_attempts:

            if self.verbose:
                print(f"Sending sw packet: {serialized_packet}")

            self.socket.sendto(serialized_packet, self.destination_address)

            # print(f"expect_ack: {expect_ack}")
            if expect_ack:
                # Wait for ACK from queue instead of socket
                try:
                    print("before get")
                    ack_packet = self.ack_queue.get(timeout=TIMEOUT)
                    print("after get")

                    if self.verbose:
                        print(f"Received ACK for sw: {ack_packet}")

                    ack_packet = StopAndWaitSegment.deserialize(ack_packet)

                    print(f"On send:received ack_num: {ack_packet.ack_num},"
                          f" self.seq: {self.seq}")

                    if ack_packet.ack_num == self.seq:
                        # Package received successfully
                        self.seq = 1 - self.seq
                        self.send_attempts = 0
                        return
                    else:
                        # The ACK is not what I expect
                        # Debug
                        print(
                            "[StopAndWaitW] Duplicate or corrupt package:"
                            f"{ack_packet}")
                    print(f"On send: ending self.seq: {self.seq}")

                except Empty:
                    print("[StopAndWait] Timeout waiting for ACK")  # Debug
            else:
                self.seq = 1 - self.seq
                print(f"On send: Not expecting ack, ending self.seq: {self.seq}")
                return
            self.send_attempts += 1

        # exited the while, the packet could not be sent -> the program closes
        raise MaxSendAttemptsExceeded(
            f"The packet with seq {self.seq} could not be sent"
            f" after {MAX_ATTEMPTS} attempts."
        )

    def put_ack_bytes(self, ack_data):
        """Put an ACK packet into the queue"""
        print(f"Putting ack bytes into sw: {ack_data}")
        self.ack_queue.put(ack_data)

    def unpack(self, serialized_data: bytes) -> tuple[bool, StopAndWaitSegment,
                                                      bytes]:
        """
        Receive sw package and deserializes, return bytes for ack
        """
        deserialized_data = StopAndWaitSegment.deserialize(serialized_data)
        print(f"SW payload received: {deserialized_data.payload}")

        print(f"Starting unpack: Received seq_num: {deserialized_data.seq_num},"
              f" ack: {self.ack}")

        if deserialized_data.seq_num == self.ack:
            # Expected packet
            # Send ACK
            ack_packet = StopAndWaitSegment(ack_num=self.ack)
            is_repeated = False

            # self.socket.sendto(serialized_ack, address)
            new_ack_num = self.ack
            self.ack = 1 - self.ack

        else:
            # Duplicate or out-of-order packet
            if not self.quiet:
                print("[SERVER] Duplicate or corrupt"
                      f"package: {deserialized_data}")
            new_ack_num = 1 - self.ack
            is_repeated = True
            # send the last ACK I received

        ack_packet = StopAndWaitSegment(ack_num=new_ack_num)
        ack_bytes = ack_packet.serialize()
        # self.socket.sendto(serialized_ack, address)

        # raise PacketDuplicateOrCorrupted(
        #     f"Expected: {self.ack}, Received: {packet.seq_num}"
        # )

        print(f"Ending unpack: Received seq_num: {deserialized_data.seq_num},"
              f" ack: {self.ack}")

        return (is_repeated, deserialized_data, ack_bytes)

    # def send_file(self, file_path):
    #     file_manager = FileManager(file_path, READ_MODE)
    #     file_manager.open()
    #     file_size = file_manager.file_size()

    #     while file_size > 0:
    #         data = file_manager.read()
    #         self.send(data)
    #         file_size -= len(data)

    #     file_manager.close()

    #     self.send(b"", eof=1)  # Send EOF

    def receive_file(self, data_bytes) -> tuple[bytes, bool, bool]:
        """
        Receives sw data bytes and responds to the message,
        returns a tuple of bool:
            - 0: Indicates if the payload is repeated
            - 1: Indicates if the received datagram indicates EOF
        """

        (is_repeated, data, ack_bytes) = self.unpack(data_bytes)
        is_eof = False

        try:
            if data.eof_num == 1:
                # print(f"[{self.actorName}] EOF received.")
                print("EOF received.")
                is_eof = True

            if self.verbose:
                print(f"sw ACK bytes: {ack_bytes}")
            if not self.quiet:
                print(f"Sending sw ACK to: {self.destination_address}")

            self.socket.sendto(ack_bytes, self.destination_address)

        except Exception as e:
            print(f"[{self.actorName}] Error receiving: {e}")  # Debug

        return (data.payload, is_repeated, is_eof)
