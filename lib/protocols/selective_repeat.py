import socket
import time
import queue
import threading
from lib.utils.constants import TIMEOUT
from lib.utils.segments import SelectiveRepeatSegment as Segment
from lib.exceptions import PacketDuplicateOrCorrupted


class SelectiveRepeat:
    def __init__(self, socket, address, verbose=False, quiet=True):
        self.socket = socket
        self.address = address
        self.verbose = verbose
        self.quiet = quiet

        # Tamaño de la ventana deslizante
        self.window_size = 4

        # El paquete con num secuencia más chico sin ACK recibido
        self.send_base = 0

        # El siguiente número de secuencia
        self.next_seq_num = 0

        # Buffer con los paquetes serializados ya enviados
        self.send_buffer = {}

        # Buffer con Timer para cada paquete
        self.time_sent = {}

        # Buffer con ACKs recibidos
        self.ack_received = {}

        # El siguiente número de secuencia que un receptor espera (ordenado)
        self.expected_seq_num = 0

        # Buffer de paquetes que llegaron pero no están ordenados (seq number)
        self.recv_buffer = {}

        # Cola interna para almacenar datagramas UDP entrantes (solo DATA)
        self.communication_queue = queue.Queue()

        # Número de secuencia que contenía el EOF
        self.final_seq_num = None

        # Estado de ejecución
        self.running = True

        # Hilo para retransmisión
        self.retransmit_thread = threading.Thread(target=self.retransmit_watcher, daemon=True)
        self.retransmit_thread.start()

    def send(self, payload, eof=0):
        while self.next_seq_num >= self.send_base + self.window_size:
            time.sleep(0.01)

        segment = Segment(
            payload=payload,
            seq_num=self.next_seq_num,  # SIN mod 256, usamos 16 bits
            ack_num=0,
            win_size=self.window_size,
            eof_num=eof
        )
        serialized = segment.serialize()

        seq = self.next_seq_num
        self.send_buffer[seq] = serialized
        self.time_sent[seq] = time.time()
        self.ack_received[seq] = False

        if self.verbose:
            print(f"[SelectiveRepeat] Enviando seq={seq}, eof={eof}")

        self.socket.sendto(serialized, self.address)
        self.next_seq_num += 1

    def handle_ack(self, segment: Segment):
        ack_num = segment.ack_num
        for seq in self.send_buffer:
            if ack_num == seq:
                self.ack_received[seq] = True
                if self.verbose:
                    print(f"[SelectiveRepeat] ACK recibido para seq={seq}")
                while self.ack_received.get(self.send_base, False):
                    self.send_base += 1
                break

    def retransmit_watcher(self):
        while self.running:
            now = time.time()
            for seq in list(self.send_buffer):
                if not self.ack_received.get(seq, False):
                    if now - self.time_sent[seq] > TIMEOUT:
                        self.socket.sendto(self.send_buffer[seq], self.address)
                        self.time_sent[seq] = now
                        if self.verbose:
                            print(f"[SelectiveRepeat] Retransmitiendo seq={seq}")
            time.sleep(0.01)

    def put_bytes(self, data: bytes):
        try:
            segment = Segment.deserialize(data)
            if segment.payload == b"" and segment.eof_num == 0:
                self.handle_ack(segment)
            else:
                if self.verbose:
                    print(f"[SelectiveRepeat] put_bytes: encolando DATA de {len(segment.payload)} bytes")
                self.communication_queue.put(data)
        except Exception as e:
            if self.verbose:
                print(f"[SelectiveRepeat] Error al procesar segmento entrante: {e}")

    def receive_file(self, data_bytes) -> tuple[bytes, bool, bool]:
        try:
            segment = Segment.deserialize(data_bytes)
            seq = segment.seq_num
            is_eof_flag = segment.eof_num == 1
            is_repeated = seq < self.expected_seq_num or seq in self.recv_buffer

            if self.verbose:
                print(f"[SelectiveRepeat] Recibido seq={seq}, eof={is_eof_flag}, repetido={is_repeated}")

            if is_eof_flag:
                self.final_seq_num = seq

            if is_repeated:
                if self.verbose:
                    print(f"[SelectiveRepeat] Ignorando paquete duplicado seq={seq}")
            else:
                if seq == self.expected_seq_num:
                    self.expected_seq_num += 1
                    while self.expected_seq_num in self.recv_buffer:
                        self.recv_buffer.pop(self.expected_seq_num)
                        self.expected_seq_num += 1
                elif seq > self.expected_seq_num:
                    self.recv_buffer[seq] = segment

            ack = Segment(ack_num=seq)
            self.socket.sendto(ack.serialize(), self.address)

            all_received = (
                self.final_seq_num is not None
                and self.final_seq_num < self.expected_seq_num
                and not self.recv_buffer
            )
            return (segment.payload, is_repeated, all_received)

        except Exception as e:
            print(f"[SelectiveRepeat] Error: {e}")
            return (b"", False, False)

    def stop(self):
        self.running = False
        self.retransmit_thread.join(timeout=1)
