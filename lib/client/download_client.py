from .base_client import BaseClient, TransferConfig
from ..utils.file_manager import FileManager
from ..utils.constants import DOWNLOAD_OPERATION, WRITE_MODE


class DownloadClient(BaseClient):
    def __init__(self, config: TransferConfig):
        super().__init__(config, DOWNLOAD_OPERATION)
        self.file_manager = None

    def data_worker(self):
        """Worker thread that writes received data to file"""
        try:
            self.file_manager = FileManager(self.config.file_path, WRITE_MODE)
            self.file_manager.open()

            while True:
                data = self.data_queue.get()
                if data is None:  # Signal to stop
                    break

                if data == b"EOF":
                    print("Download complete")
                    break

                self.file_manager.write(data)

            self.transfer_complete.set()

        except Exception as e:
            self.error = f"Error writing file: {str(e)}"
            self.transfer_complete.set()
        finally:
            if self.file_manager:
                self.file_manager.close()

    def protocol_worker(self):
        """Worker thread that handles protocol and receives data"""
        try:
            while True:
                try:
                    data = self.protocol_handler.receive_file()
                    self.data_queue.put(data)

                    if data == b"EOF":
                        break

                except Exception as e:
                    if self.config.verbose:
                        print(f"Error receiving data: {e}")
                    continue

        except Exception as e:
            self.error = f"Protocol error: {str(e)}"
            self.data_queue.put(None)  # Signal data worker to stop
            self.transfer_complete.set()
