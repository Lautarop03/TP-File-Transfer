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
        self.communication_queue = Queue()  # Queue for receiving ACKs
        self.waiting_ack = False

    def send(self, payload, eof=0):  # Send a single package
        SW_segment = StopAndWaitSegment(
            payload=payload, seq_num=self.seq, eof_num=eof)

        serialized_packet = SW_segment.serialize()

        while MAX_ATTEMPTS > self.send_attempts:

            if self.verbose:
                print(f"Sending SW packet: {serialized_packet}")

            self.socket.sendto(serialized_packet, self.destination_address)

            try:
                print("On send: before get from communication_queue")
                self.waiting_ack = True
                ack_packet = self.communication_queue.get(timeout=TIMEOUT)
                print("On send: after get from communication_queue")

                if self.verbose:
                    print(f"Received ACK for SW. Bytes: {ack_packet}")

                ack_packet = StopAndWaitSegment.deserialize(ack_packet)
                print(f"recibo ack: {ack_packet.ack_num}"
                      f" y mande seq: {self.seq}")
                if ack_packet.ack_num == self.seq:
                    # Package received successfully
                    self.send_attempts = 0
                    self.seq = 1 - self.seq
                    self.waiting_ack = False
                    return
                else:
                    # The ACK is not what I expect
                    # Debug
                    print(
                        "[StopAndWaitW] Duplicate or corrupt package:"
                        f"{ack_packet}")

            except Empty:
                print("[StopAndWait] Timeout waiting for ACK")  # Debug

            self.send_attempts += 1

        # exited the while, the packet could not be sent -> the program closes
        raise MaxSendAttemptsExceeded(
            f"The packet with seq {self.seq} could not be sent"
            f" after {MAX_ATTEMPTS} attempts."
        )

    def put_bytes(self, data):
        """Put an ACK packet into the queue"""
        print(f"Putting {len(data)} bytes into SW communication queue")
        self.communication_queue.put(data)

    def unpack(self, serialized_data: bytes) -> tuple[bool, StopAndWaitSegment,
                                                      bytes]:
        """
        Receive SW package and deserializes, return bytes for ack
        """
        deserialized_data = StopAndWaitSegment.deserialize(serialized_data)

        if deserialized_data.seq_num == self.ack:
            # Expected packet
            # Send ACK
            ack_packet = StopAndWaitSegment(ack_num=self.ack)
            is_repeated = False

            # self.socket.sendto(serialized_ack, address)
            self.ack = 1 - self.ack
            new_ack_num = self.ack

        else:
            # Duplicate or out-of-order packet
            if not self.quiet:
                print("Duplicate or corrupt"
                      f"package: {deserialized_data}")
            new_ack_num = 1 - self.ack
            is_repeated = True
            # send the last ACK I received
            ack_packet = StopAndWaitSegment(ack_num=new_ack_num)

        ack_bytes = ack_packet.serialize()

        print(f"Ending unpack: Received seq_num: {deserialized_data.seq_num},"
              f" ack: {new_ack_num}")

        return (is_repeated, deserialized_data, ack_bytes)

    def receive_file(self, data_bytes) -> tuple[bytes, bool, bool]:
        """
        Receives SW data bytes and responds to the message,
        returns a tuple of bool:
            - 0: Indicates if the payload is repeated
            - 1: Indicates if the received datagram indicates EOF
        """

        (is_repeated, data, ack_bytes) = self.unpack(data_bytes)
        is_eof = False

        try:
            if data.eof_num == 1:
                print("EOF received.")
                is_eof = True

            if self.verbose:
                print(f"SW ACK bytes: {ack_bytes}")
            if not self.quiet:
                print(f"Sending SW ACK to: {self.destination_address}")

            self.socket.sendto(ack_bytes, self.destination_address)

        except Exception as e:
            print(f"[{self.actorName}] Error receiving: {e}")  # Debug

        return (data.payload, is_repeated, is_eof)
