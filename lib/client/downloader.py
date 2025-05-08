from queue import Queue
import queue
import socket
import threading
from lib.utils.static import (
    get_protocol_from_args,
    get_protocol_code_from_protocol_str)
from ..utils.file_manager import FileManager
from ..utils.constants import (
    APPEND_MODE, BUFFER_SIZE, DOWNLOAD_OPERATION,
    EOF_MARKER, MAX_ATTEMPTS)


class Downloader():
    def __init__(self, args, is_client: bool):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.destination_address = (args.host, args.port)
        self.protocol_handler = get_protocol_from_args(
            args, self.socket, self.destination_address)
        self.data_queue = Queue()
        self.error = None
        self.op_code = DOWNLOAD_OPERATION
        self.protocol_code = get_protocol_code_from_protocol_str(args.protocol)
        self.file_name = args.name  # solo lo usa el cliente en init
        self.file_path = args.dst
        self.file_manager = FileManager(args.dst, APPEND_MODE)
        self.file_manager.open()
        self.is_client = is_client
        self.verbose = args.verbose
        self.quiet = args.quiet
        self.data_worker_thread = threading.Thread(target=self.data_worker)
        self.data_worker_thread.daemon = True
        self.data_worker_thread.start()

    def data_worker(self):
        """Worker thread that writes received data to file"""
        if self.verbose:
            print("[Downloader] Data worker start, "
                  f"writing to: {self.file_manager.path}")
        try:

            while True:
                data_bytes = self.data_queue.get()

                if self.error is not None:
                    break

                if data_bytes is None:  # Signal to ignore
                    continue

                if data_bytes is EOF_MARKER:
                    if not self.quiet:
                        print("[Downloader] Download complete")
                    break

                self.file_manager.append(data_bytes)

        except Exception as e:
            self.error = f"Error writing file in download: {str(e)}"

    def protocol_worker(self, result_queue):
        """
        Worker thread that handles protocol and receives data
        """
        if self.verbose:
            print("[Downloader] Protocol worker start")

        try:
            data_bytes = self.protocol_handler.communication_queue.get()
            data, is_repeated, is_eof = self.protocol_handler.receive_file(
                data_bytes)

            if is_repeated:
                data = None

            if is_eof:
                data = EOF_MARKER

            self.data_queue.put(data)

            result_queue.put(is_eof)  # Siempre le mando, sino bloquea

        except Exception as e:
            self.error = f"[Downloader] Protocol error: {str(e)}"
            self.data_queue.put("")  # Signal data worker to stop

    def transfer(self, is_client=True):
        if is_client:
            self.transfer_for_client()
        else:
            self.start_workers(queue.Queue())

    def transfer_for_client(self):
        result_queue = queue.Queue()
        is_finished = False
        timeout_counter = 0
        self.socket.settimeout(5)  # timeout for server response
        try:
            while not is_finished:
                try:
                    # Receive data
                    if not self.quiet:
                        print("[CLIENT] Waiting for data...")
                    data, _ = self.socket.recvfrom(BUFFER_SIZE)
                    if not self.quiet:
                        print("[CLIENT] Processing data")
                    self.protocol_handler.put_bytes(data)
                    # Reset timeout counter on successful receive
                    timeout_counter = 0
                except socket.timeout:
                    timeout_counter += 1
                    if timeout_counter >= MAX_ATTEMPTS:
                        print("[CLIENT] Error: Maximum number of timeouts "
                              f"({MAX_ATTEMPTS}) reached. Aborting transfer.")
                        e = f"Connection timeout after {MAX_ATTEMPTS} attempts"
                        self.error = e
                        break
                    if not self.quiet:
                        print("[CLIENT] Timeout waiting for server message..."
                              f" ({timeout_counter}/{MAX_ATTEMPTS})")
                    continue

                self.start_workers(result_queue)

                is_finished = result_queue.get()

            print("[CLIENT] Transfer complete")
        except KeyboardInterrupt:
            print("\nClient interruption. Closing connection gracefully\n")
        finally:
            self.file_manager.close()
            self.socket.sendto(b"FIN", self.destination_address)
            if self.verbose:
                print("[CLIENT] Sending FIN to server")
            self.socket.close()

    def start_workers(self, result_queue):
        protocol_thread = threading.Thread(target=self.protocol_worker,
                                           args=(result_queue,))

        protocol_thread.daemon = True

        protocol_thread.start()

    def terminate(self):
        self.file_manager.close()
        self.data_worker_thread.join(timeout=1)
