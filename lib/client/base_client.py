import socket
import threading
from dataclasses import dataclass
from queue import Queue
from ..protocols.stop_and_wait import StopAndWait
# TODO: Import when implemented
# from protocols.selective_repeat import SelectiveRepeat
from ..utils.constants import BUFFER_SIZE
from ..utils.segments import InitSegment


@dataclass
class TransferConfig:
    server_host: str
    server_port: int
    file_path: str
    is_download: bool
    protocol_code: int  # STOP_AND_WAIT or SELECTIVE_REPEAT
    verbose: bool = False


class BaseClient:
    def __init__(self, config: TransferConfig, op_code):
        self.config = config
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.protocol_handler = None
        self.data_queue = Queue()  # For transferring data between threads
        self.transfer_complete = threading.Event()
        self.error = None
        self.op_code = op_code

    def init_connection(self, verbose) -> bool:
        """Initialize connection with server"""
        try:
            # Create and send INIT message
            init_segment = InitSegment(self.op_code, self.config.protocol_code,
                                       0b0, self.config.file_path)

            init_message = init_segment.serialize(verbose)

            self.socket.sendto(
                init_message, (self.config.server_host,
                               self.config.server_port))

            # Wait for server response
            self.socket.settimeout(5)  # 5 seconds timeout for INIT response
            response, _ = self.socket.recvfrom(BUFFER_SIZE)

            if response.startswith(b"ERROR:"):
                self.error = response.decode('utf-8')
                return False

            if response != b"INIT_ACK":
                self.error = f"Unexpected server response: {response}"
                return False

            # Create appropriate protocol handler
            if self.config.protocol == "sw":
                self.protocol_handler = StopAndWait(
                    self.socket,
                    self.config.server_host,
                    self.config.server_port
                )
            else:
                # TODO: Implement SelectiveRepeat handler
                self.error = "Selective Repeat protocol not implemented yet"
                return False

            return True

        except Exception as e:
            self.error = f"Connection initialization failed: {str(e)}"
            return False

    def data_worker(self):
        """Abstract method to be implemented by subclasses"""
        raise NotImplementedError

    def protocol_worker(self):
        """Abstract method to be implemented by subclasses"""
        raise NotImplementedError

    def start_transfer(self):
        """Start the file transfer process"""
        if not self.init_connection():
            if self.config.verbose:
                print(f"Failed to initialize connection: {self.error}")
            return False

        # Start worker threads
        data_thread = threading.Thread(target=self.data_worker)
        protocol_thread = threading.Thread(target=self.protocol_worker)

        data_thread.daemon = True
        protocol_thread.daemon = True

        data_thread.start()
        protocol_thread.start()

        # Wait for transfer to complete
        self.transfer_complete.wait()

        # Check for errors
        if self.error:
            if self.config.verbose:
                print(f"Transfer failed: {self.error}")
            return False

        return True

    def cleanup(self):
        """Clean up resources"""
        self.socket.close()
