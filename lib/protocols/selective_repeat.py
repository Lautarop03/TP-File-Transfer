import socket
import time
from lib.utils.constants import TIMEOUT, BUFFER_SIZE, READ_MODE, APPEND_MODE
from lib.utils.file_manager import FileManager
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

        # El paquete con num secuencia mas chico sin ACK recibido
        self.send_base = 0

        # El siguiente numero de secuencia
        self.next_seq_num = 0

        # Buffer con los paquetes serializados ya enviados
        self.send_buffer = {}

        # Buffer con los ACK recibidos
        self.ack_received = {}

        # Buffer con Timer para cada paquete
        self.time_sent = {}

        # El siguiente numero de secuencia que un receptor espera (ordenado)
        self.expected_seq_num = 0

        # Buffer de paquetes que llegaron pero no estan ordenados (seq number)
        self.recv_buffer = {}

    def send(self, payload, eof=0):
        # Si el numero de secuencia enviado es mas grande/igual
        # que el tamaño de la ventana + el paquete mas chico enviado sin ACK
        # Entonces no puedo seguir enviando, chequeo TIME OUT's de los enviados
        if self.next_seq_num >= self.send_base + self.window_size:
            self._check_timeouts()
            return

        # Si tengo espacio en la ventana, creo un segmento
        segment = Segment(
            payload=payload,
            seq_num=self.next_seq_num % 256, # Ciclo de 256 numeros de secuencia
            ack_num=0,
            win_size=self.window_size,
            eof_num=eof
        )
        serialized = segment.serialize()

        # Guardo en el buffer de paquetes enviados sin ACK
        # el paquete que voy a enviar
        self.send_buffer[self.next_seq_num] = serialized

        # Marco en el buffer de ACK's ese paquete
        self.ack_received[self.next_seq_num] = False

        # Empiezo a controlar el tiempo del paquete
        self.time_sent[self.next_seq_num] = time.time()

        if self.verbose:
            print(f"[SelectiveRepeat] Enviando paquete seq={self.next_seq_num}, eof={eof}")

        # Envio
        self.socket.sendto(serialized, self.address)
        self.next_seq_num += 1

    def _check_timeouts(self):
        """
        Este procedimiento controla que los paquetes que no fueron
        ACKeados, no se hayan pasado por TIME OUT. 

        Si el paquete vencio por tiempo, entonces lo reenvia
        """
        now = time.time()
        for seq, sent_time in list(self.time_sent.items()):
            if not self.ack_received[seq] and (now - sent_time > TIMEOUT):
                if self.verbose:
                    print(f"[SelectiveRepeat] Reenviando seq={seq} por timeout")
                self.socket.sendto(self.send_buffer[seq], self.address)
                self.time_sent[seq] = now

    def receive_ack_loop(self):
        """
        Espera los ACK, al recibir uno lo deserializa 
        y marca en el Buffer de ACK's que recibimos
        el paquete Buffer[seq_number]
        """
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
                            print(f"[SelectiveRepeat] ACK recibido para seq={seq}")
                while self.ack_received.get(self.send_base, False):
                    self.send_base += 1

        except socket.timeout:
            pass

    def receive_file(self, data_bytes) -> tuple[bytes, bool, bool]:
        try:
            segment = Segment.deserialize(data_bytes)
            seq = segment.seq_num
            is_eof_flag = segment.eof_num == 1
            is_repeated = seq < self.expected_seq_num or seq in self.recv_buffer

            if self.verbose:
                print(f"[SelectiveRepeat] Recibido seq={seq}, eof={is_eof_flag}, repetido={is_repeated}")

            # Guardar el número de secuencia del EOF si se recibe
            if is_eof_flag:
                self.final_seq_num = seq

            # Si ya lo teniamos, ignoramos la parte de procesamiento
            if is_repeated:
                if self.verbose:
                    print(f"[SelectiveRepeat] Ignorando paquete duplicado seq={seq}")
            else:
                if seq == self.expected_seq_num:
                    self.expected_seq_num = (self.expected_seq_num + 1) % 256
                    while self.expected_seq_num in self.recv_buffer:
                        self.recv_buffer.pop(self.expected_seq_num)
                        self.expected_seq_num = (self.expected_seq_num + 1) % 256
                elif seq > self.expected_seq_num:
                    self.recv_buffer[seq] = segment

            # Enviar ACK
            ack = Segment(ack_num=seq)
            self.socket.sendto(ack.serialize(), self.address)

            # Confirmar si se puede cerrar
            all_received = (
                hasattr(self, "final_seq_num")
                and self.final_seq_num < self.expected_seq_num
                and not self.recv_buffer
            )
            return (segment.payload, is_repeated, all_received)

        except Exception as e:
            print(f"[SelectiveRepeat] Error: {e}")
            return (b"", False, False)

