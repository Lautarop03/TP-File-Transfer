import socket
import time
from lib.utils.constants import TIMEOUT, BUFFER_SIZE, MAX_ATTEMPTS, READ_MODE, APPEND_MODE
from lib.utils.file_manager import FileManager
from lib.utils.segments import SelectiveRepeatSegment as Segment
from lib.exceptions import MaxSendAttemptsExceeded, PacketDuplicateOrCorrupted


class SelectiveRepeat:
    def __init__(self, socket, address, verbose=False, quiet=True):
        self.socket = socket
        self.address = address
        self.verbose = verbose
        self.quiet = quiet

        self.window_size = 4
        self.send_base = 0
        self.next_seq_num = 0

        self.send_buffer = {}       # seq_num -> segment (bytes)
        self.ack_received = {}      # seq_num -> bool
        self.time_sent = {}         # seq_num -> float

        self.expected_seq_num = 0
        self.recv_buffer = {}

    def send(self, payload, eof=0):
        if self.next_seq_num >= self.send_base + self.window_size:
            self._check_timeouts()
            return  # Ventana llena: no enviar más

        segment = Segment(
            payload=payload,
            seq_num=self.next_seq_num % 256,
            ack_num=0,
            win_size=self.window_size
        )
        serialized = segment.serialize()
        self.send_buffer[self.next_seq_num] = serialized
        self.ack_received[self.next_seq_num] = False
        self.time_sent[self.next_seq_num] = time.time()

        if self.verbose:
            print(f"[SR SEND] Enviando seq {self.next_seq_num}: {serialized}")

        self.socket.sendto(serialized, self.address)
        self.next_seq_num += 1

    def _check_timeouts(self):
        now = time.time()
        for seq, sent_time in list(self.time_sent.items()):
            if not self.ack_received[seq] and (now - sent_time > TIMEOUT):
                if self.verbose:
                    print(f"[SR TIMEOUT] Reenviando seq {seq}")
                self.socket.sendto(self.send_buffer[seq], self.address)
                self.time_sent[seq] = now

    def receive_ack_loop(self):
        try:
            self.socket.settimeout(0.01)
            while True:
                data, _ = self.socket.recvfrom(BUFFER_SIZE)
                ack_segment = Segment.deserialize(data)
                ack_num = ack_segment.ack_num

                for seq in self.ack_received:
                    if ack_num == (seq % 256):
                        self.ack_received[seq] = True
                        if self.verbose:
                            print(f"[SR ACK] Recibido ACK para seq {seq}")
        except socket.timeout:
            pass

    def receive(self):
        while True:
            data, addr = self.socket.recvfrom(BUFFER_SIZE)
            segment = Segment.deserialize(data)
            seq = segment.seq_num

            ack = Segment(ack_num=seq)
            self.socket.sendto(ack.serialize(), addr)

            if self.verbose:
                print(f"[SR RECEIVE] Recibido seq {seq}, esperado {self.expected_seq_num}")

            if seq == self.expected_seq_num:
                entregables = [segment]
                self.expected_seq_num = (self.expected_seq_num + 1) % 256

                while self.expected_seq_num in self.recv_buffer:
                    entregables.append(self.recv_buffer.pop(self.expected_seq_num))
                    self.expected_seq_num = (self.expected_seq_num + 1) % 256

                for seg in entregables:
                    return seg

            elif seq > self.expected_seq_num:
                if seq not in self.recv_buffer:
                    self.recv_buffer[seq] = segment

            else:
                if self.verbose:
                    print(f"[SR RECEIVE] Duplicado: {seq}")

    def send_file(self, file_path):
        fm = FileManager(file_path, READ_MODE)
        fm.open()
        file_size = fm.file_size()

        while file_size > 0 or any(not v for v in self.ack_received.values()):
            if file_size > 0:
                data = fm.read(BUFFER_SIZE)
                self.send(data)
                file_size -= len(data)

            self.receive_ack_loop()
            self._check_timeouts()
            time.sleep(0.01)

        fm.close()
        self.send(b"", eof=1)

    def receive_file(self, path):
        fm = FileManager(path, APPEND_MODE)
        fm.open()

        while True:
            try:
                segment = self.receive()
                fm.append(segment.payload)

                if segment.payload == b"FIN" or segment.seq_num == 0xFFFF:
                    break

            except PacketDuplicateOrCorrupted:
                continue

        fm.close()
        if self.verbose:
            print("[SR] Archivo recibido correctamente.")
