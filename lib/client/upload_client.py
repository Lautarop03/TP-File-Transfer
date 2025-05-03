from .base_client import BaseClient, TransferConfig
from ..utils.file_manager import FileManager
from ..utils.constants import READ_MODE, BUFFER_SIZE, UPLOAD_OPERATION


class UploadClient(BaseClient):
    def __init__(self, config: TransferConfig):
        super().__init__(config, UPLOAD_OPERATION)
        self.file_manager = FileManager(self.config.file_path, READ_MODE)

    def data_worker(self):
        """Worker thread that reads data from file"""
        print(f"Data worker start, reading from:{self.file_manager.path}")
        try:
            self.file_manager.open()
            file_size = self.file_manager.file_size()
            print(f"Data worker, size is:{file_size}")

            while file_size > 0:
                print("Start to read file")
                data = self.file_manager.read(BUFFER_SIZE)
                print(f"Read file on data worker: {data}")
                self.data_queue.put(data)
                file_size -= len(data)
                # TODO: The protocol must create the message here
                # REVIEW if data queue is needed...

            # Signal end of file
            self.data_queue.put(b"EOF")

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
                    # If data is a string (error message), encode it
                    if isinstance(data, str):
                        data = data.encode()
                    
                    # Send data in chunks that fit within the buffer size
                    chunk_size = BUFFER_SIZE - 7  # Account for header size
                    for i in range(0, len(data), chunk_size):
                        chunk = data[i:i + chunk_size]
                        self.protocol_handler.send(chunk)

                    if data == b"EOF":
                        # Send EOF packet
                        self.protocol_handler.send(b"", eof=1)
                        if self.config.verbose:
                            print("Upload complete")
                        break

                except Exception as e:
                    if self.config.verbose:
                        print(f"Error sending data: {e}")
                    # For upload, we should stop on protocol errors
                    self.error = f"Protocol error: {str(e)}"
                    break

            self.transfer_complete.set()

        except Exception as e:
            self.error = f"Protocol error: {str(e)}"
            self.transfer_complete.set()
