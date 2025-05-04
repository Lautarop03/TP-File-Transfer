from ..utils.constants import (
    DATA_SIZE, EOF_MARKER, READ_MODE, UPLOAD_OPERATION)
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
        self.is_download = False
        # self.config = get_transfer_config_from_args(
        # args, args.name, args.src)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.transfer_complete = threading.Event()
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
        self.verbose = args.verbose
        self.quiet = args.quiet

    def data_worker(self):
        """Worker thread that reads data from file"""
        print(f"Data worker start, reading from: {self.file_manager.path}")
        try:
            self.file_manager.open()
            file_size = self.file_manager.file_size()
            print(f"Data worker, file size is: {file_size}")

            while file_size > 0:
                print("Start to read file")
                data = self.file_manager.read(DATA_SIZE)
                print(f"Read file on data worker: {data}")
                self.data_queue.put(data)
                file_size -= len(data)

            self.data_queue.put(EOF_MARKER)

        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            self.error = error_msg
            # Send error as bytes through the queue
            self.data_queue.put(error_msg.encode())
            self.transfer_complete.set()
        finally:
            if self.file_manager:
                self.file_manager.close()

    def protocol_worker(self):
        """Worker thread that handles protocol and sends data"""
        try:
            print("protocol worker start")
            while True:
                data = self.data_queue.get()
                print(f"Protocol worker: {data}")
                if data is None:  # Error signal
                    break

                try:
                    if data == EOF_MARKER:
                        # Send EOF packet
                        self.protocol_handler.send(b"", eof=1)
                        if self.verbose:
                            print("Upload complete")
                        break
                    self.protocol_handler.send(data)

                except Exception as e:
                    if self.verbose:
                        print(f"Error sending data: {e}")
                    # For upload, we should stop on protocol errors
                    self.error = f"Protocol error: {str(e)}"
                    break

            self.transfer_complete.set()

        except Exception as e:
            self.error = f"Protocol error: {str(e)}"
            self.transfer_complete.set()

    def transfer(self, _):

        # if is_client:
        #     # lo que ya esta
        # else:
        #     # queue simulando socket?
        data_thread = threading.Thread(target=self.data_worker)
        protocol_thread = threading.Thread(target=self.protocol_worker)

        data_thread.daemon = True
        protocol_thread.daemon = True

        data_thread.start()
        protocol_thread.start()

        self.transfer_complete.wait()

        self.socket.close()

        return True
