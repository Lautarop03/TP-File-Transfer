import queue
from ..utils.constants import (
    BUFFER_SIZE, EOF_MARKER, READ_MODE, UPLOAD_OPERATION)
from ..utils.file_manager import FileManager
import os
from queue import Queue
import socket
import threading

from lib.utils.static import (
    get_protocol_from_args,
    get_protocol_code_from_protocol_str)


class Uploader():
    def __init__(self, args):

        if not args.src or not os.path.exists(args.src):
            print(f"ERROR: Source file not found: {args.src}")
            raise FileNotFoundError
        if args.verbose:
            print(f"[Uploader] File {args.src} found for upload")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.destination_address = (args.host, args.port)
        self.protocol_handler = get_protocol_from_args(
            args, self.socket, self.destination_address)
        self.data_queue = Queue()
        self.error = None
        self.op_code = UPLOAD_OPERATION
        self.protocol_code = get_protocol_code_from_protocol_str(args.protocol)
        self.file_name = args.name  # solo lo usa el cliente en init
        self.file_path = args.src
        self.file_manager = FileManager(args.src, READ_MODE)
        self.file_manager.open()
        self.current_size_remaining = self.file_manager.file_size()
        self.verbose = args.verbose
        self.quiet = args.quiet
        self.data_worker_thread = threading.Thread(target=self.data_worker)
        self.data_worker_thread.daemon = True
        self.data_worker_thread.start()

    def data_worker(self):
        """Worker thread that reads data from file"""
        if self.verbose:
            print("[Uploader] Data worker start, "
                  f"reading from: {self.file_manager.path}")
        try:
            data_size = BUFFER_SIZE - self.protocol_handler.header_size
            while True:
                if self.current_size_remaining > 0:
                    data = self.file_manager.read(data_size)
                    self.data_queue.put(data)
                    self.current_size_remaining -= len(data)
                else:
                    self.data_queue.put(EOF_MARKER)
                    break

        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            self.error = error_msg
            # Send error as bytes through the queue
            self.data_queue.put(error_msg.encode())

    def protocol_worker(self, result_queue):
        """Worker thread that handles protocol and sends data"""
        if self.verbose:
            print("[Uploader] Protocol worker start")
        try:

            data = self.data_queue.get()
            if data is None:
                result_queue.put(True)

            try:
                if data is EOF_MARKER:
                    # Send EOF packet
                    self.protocol_handler.send(
                        b"", eof=1)
                    if self.verbose:
                        print("[Uploader] Upload complete")
                    result_queue.put(True)
                else:
                    self.protocol_handler.send(
                        data, eof=0)
                    result_queue.put(False)

            except Exception as e:
                if self.verbose:
                    print(f"Error sending data: {e}")
                # For upload, we should stop on protocol errors
                self.error = f"Protocol error: {str(e)}"
                result_queue.put(True)

        except Exception as e:
            self.error = f"Protocol error: {str(e)}"
            raise e

    def transfer(self, is_client=True):
        result_queue = queue.Queue()
        if is_client:
            self.transfer_all_here(result_queue)
        else:
            self.start_workers(result_queue)
            result = result_queue.get()
            return result

    def transfer_all_here(self, result_queue):
        is_finished = False
        self.socket.settimeout(5)  # timeout for server response
        try:
            while not is_finished:
                self.start_workers(result_queue)
                try:
                    # Receive data
                    if not self.quiet:
                        print("[CLIENT] Waiting for server response...")
                    data, _ = self.socket.recvfrom(BUFFER_SIZE)
                    if not self.quiet:
                        print("[CLIENT] Proccesing response")
                    self.protocol_handler.put_bytes(data)
                except socket.timeout:
                    if not self.quiet:
                        print("[CLIENT] TIMEOUT while waiting for "
                              "message on uploader...")
                    continue
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
                                           args=(result_queue, ))

        protocol_thread.daemon = True

        protocol_thread.start()

    def terminate(self):
        self.file_manager.close()
        self.data_worker_thread.join(timeout=1)
