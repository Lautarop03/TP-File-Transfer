import socket
import threading
from dataclasses import dataclass
from queue import Queue
from ..protocols.stop_and_wait import StopAndWait
# TODO: Import when implemented
# from protocols.selective_repeat import SelectiveRepeat
from ..utils.constants import BUFFER_SIZE, STOP_AND_WAIT
from ..utils.segments import InitSegment


@dataclass
class TransferConfig:
    server_address: tuple[str, int]
    file_name: str
    file_path: str
    verbose: bool = False
    quiet: bool = False


class BaseClient:
    def __init__(self, config: TransferConfig, op_code):
        self.config = config
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.protocol_handler = None
        self.data_queue = Queue()  # For transferring data between threads
        self.transfer_complete = threading.Event()
        self.error = None
        self.op_code = op_code

    def init_connection(self, protocol, verbose, quiet) -> bool:
        """Initialize connection with server"""
        try:
            if not quiet:
                print("Initiating connection with server")

            # Create and send INIT message
            init_segment = InitSegment(self.op_code, protocol,
                                       0b0, self.config.file_name)

            init_message = init_segment.serialize(verbose)

            if verbose:
                print(f"Created init message with data: {init_message}")
                print("Trying to connect with server running on "
                      f"{self.config.server_address[0]}:"
                      f"{self.config.server_address[1]}")

            self.socket.sendto(
                init_message, self.config.server_address)

            if not quiet:
                print("Waiting for server response")

            # Wait for server response
            self.socket.settimeout(5)  # 5 seconds timeout for INIT response
            response, _ = self.socket.recvfrom(BUFFER_SIZE)

            if not quiet:
                print("Received server response")

            if verbose:
                print(f"Received bytes: {response}")

            init_segment = InitSegment.deserialize(response, verbose)
            if not init_segment.ack == 0b1:
                self.error = "Response from server is not ACK"
                return False

            # Create appropriate protocol handler
            if protocol == STOP_AND_WAIT:
                self.protocol_handler = StopAndWait(
                    self.socket,
                    self.config.server_address,
                    verbose,
                    quiet
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

    def start_transfer(self) -> bool:
        """Start the file transfer process"""
        # if not self.init_connection():
        #     self.error = "Failed to initialize connection"
        #     return False

        # Start worker threads
        data_thread = threading.Thread(target=self.data_worker)
        protocol_thread = threading.Thread(target=self.protocol_worker)

        data_thread.daemon = True
        protocol_thread.daemon = True

        data_thread.start()
        protocol_thread.start()

        # Wait for transfer to complete
        self.transfer_complete.wait()

        if not self.config.quiet:
            print("Gracefully shutting down connection")

        self.socket.sendto("FIN", self.config.server_address)
        self.socket.close()

        print("Gracefully shut down connecion with server")

        # Check for errors
        if self.error:
            print(f"Transfer failed: {self.error}")
            return False

        return True

    def cleanup(self):
        """Clean up resources"""
        self.socket.close()
