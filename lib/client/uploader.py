import queue
from ..utils.constants import (
    BUFFER_SIZE, DATA_SIZE, EOF_MARKER, READ_MODE, UPLOAD_OPERATION)
from ..utils.file_manager import FileManager
import os
from queue import Queue
import socket
import threading

from lib.utils.static import (
    get_protocol_from_args,
    # get_transfer_config_from_args,
    get_protocol_code_from_protocol_str)
# , UPLOAD_OPERATION


class Uploader():
    def __init__(self, args):

        if not args.src or not os.path.exists(args.src):
            print(f"ERROR: Source file not found: {args.src}")
            raise FileNotFoundError
        if args.verbose:
            print(f"File {args.src} found for upload")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.destination_address = (args.host, args.port)
        self.protocol_handler = get_protocol_from_args(
            args, self.socket, self.destination_address)
        self.data_queue = Queue()
        self.ack_queue = Queue()
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

    def data_worker(self):
        """Worker thread that reads data from file"""
        print(f"Data worker start, reading from: {self.file_manager.path}")
        try:
            # file_size = self.file_manager.file_size()
            # print(f"Data worker, file size is: {file_size}")

            if self.current_size_remaining > 0:
                # while file_size > 0:
                # print("Start to read file")
                data = self.file_manager.read(DATA_SIZE)
                print(f"Read file on data worker: {data}")
                self.data_queue.put(data)
                self.current_size_remaining -= len(data)
            # file_size -= len(data)
            else:
                self.data_queue.put(EOF_MARKER)

        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            self.error = error_msg
            # Send error as bytes through the queue
            self.data_queue.put(error_msg.encode())
        # finally:
        #     if self.file_manager:
        #         self.file_manager.close()

    def protocol_worker(self, result_queue, expect_ack=True):
        """Worker thread that handles protocol and sends data"""
        try:
            # print("protocol worker start")
            # while True:
            data = self.data_queue.get()
            print(f"Protocol worker: {data}")
            if data is None:
                result_queue.put(True)

            try:
                if data == EOF_MARKER:
                    # Send EOF packet
                    self.protocol_handler.send(
                        b"", eof=1, expect_ack=expect_ack)
                    if self.verbose:
                        print("Upload complete")
                    result_queue.put(True)
                self.protocol_handler.send(data, eof=0, expect_ack=expect_ack)
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

    def transfer(self, ack_bytes=None, is_kickstart=False):
        result_queue = queue.Queue()
        if ack_bytes is None:
            self.transfer_all_here(result_queue)
        else:
            if not is_kickstart:
                self.protocol_handler.put_ack_bytes(ack_bytes)
            expect_ack = not is_kickstart
            print(f"expect_ack: {expect_ack}")
            self.start_workers(result_queue, expect_ack=expect_ack)
            result = result_queue.get()
            print(f"Result: {result}")
            return result

    def transfer_all_here(self, result_queue):
        print("Transfer all here")
        is_finished = False
        iter = 0

        while not is_finished:
            iter += 1
            print(f"Iteration {iter}")
            self.start_workers(result_queue)
            try:
                # Receive data
                # Al socket le quedo el time out que se uso en init
                # self.socket.settimeout(None)  # Reset timeuot
                print("Waiting for data")
                data, _ = self.socket.recvfrom(BUFFER_SIZE)
                print(f"Received data: {data}")
                self.protocol_handler.put_ack_bytes(data)
            except socket.timeout:
                if not self.quiet:
                    print("[CLIENT] Waiting for server message...")
                continue
            print("i've data!!!!")

            is_finished = result_queue.get()

        print("Transfer all here finished")
        self.file_manager.close()
        self.socket.sendto(b"FIN", self.destination_address)
        print("Sent FIN")
        self.socket.close()

    def start_workers(self, result_queue, expect_ack=True):
        data_thread = threading.Thread(target=self.data_worker)
        protocol_thread = threading.Thread(target=self.protocol_worker,
                                           args=(result_queue, expect_ack))

        data_thread.daemon = True
        protocol_thread.daemon = True

        protocol_thread.start()
        data_thread.start()

    def close_file_manager(self):
        self.file_manager.close()
