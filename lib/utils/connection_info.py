from dataclasses import dataclass

from lib.client.downloader import Downloader
from lib.client.uploader import Uploader
from lib.utils.constants import DOWNLOAD_OPERATION
from lib.utils.segments import InitSegment


@dataclass
class ConnectionInfo:
    operation_handler: object  # Downloader or Uploader
    protocol: str     # "sw" for Stop & Wait, "sr" for Selective Repeat
    file_path: str    # For upload: filename to create,
    protocol_handler: object  # StopAndWait or SelectiveRepeat instance
    finished: bool = False

    def __init__(self, init_segment: 'InitSegment',
                 socket, client_address, args):

        # Argumentos para el operation handler
        args.name = ""
        args.host = client_address[0]
        args.port = client_address[1]
        server_path = args.storage + '/' + init_segment.name.decode("utf-8")

        if init_segment.opcode == DOWNLOAD_OPERATION:
            args.src = server_path
            operation_handler = Uploader(args)
        else:
            args.dst = server_path
            operation_handler = Downloader(args, False)

        self.operation_handler = operation_handler
        self.file_path = init_segment.name.decode("utf-8")

    def set_finished(self, finished):
        self.finished = finished

    def terminate(self):
        self.operation_handler.terminate()
