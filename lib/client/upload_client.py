from .base_client import BaseClient, TransferConfig
from ..utils.file_manager import FileManager
from ..utils.constants import READ_MODE, BUFFER_SIZE, UPLOAD_OPERATION


class UploadClient(BaseClient):
    def __init__(self, config: TransferConfig):
        super().__init__(config, UPLOAD_OPERATION)
        self.file_manager = None

    def data_worker(self):
        """Worker thread that reads data from file"""
        try:
            self.file_manager = FileManager(self.config.file_path, READ_MODE)
            self.file_manager.open()
            file_size = self.file_manager.file_size()

            while file_size > 0:
                data = self.file_manager.read(BUFFER_SIZE)
                self.data_queue.put(data)
                file_size -= len(data)
                # TODO: The protocol must create the message here
                # REVIEW if data queue is needed...

            # Signal end of file
            self.data_queue.put(b"EOF")

        except Exception as e:
            self.error = f"Error reading file: {str(e)}"
            self.data_queue.put(None)  # Signal protocol worker to stop
            self.transfer_complete.set()
        finally:
            if self.file_manager:
                self.file_manager.close()

    def protocol_worker(self):
        """Worker thread that handles protocol and sends data"""
        try:
            while True:
                data = self.data_queue.get()
                if data is None:  # Error signal
                    break

                try:
                    self.protocol_handler.send(data)

                    if data == b"EOF":
                        # TODO: EOF is a flag we need to send
                        # for the server to know
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
