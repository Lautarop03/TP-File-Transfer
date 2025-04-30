from dataclasses import dataclass

from lib.protocols.stop_and_wait import StopAndWait
from lib.utils.constants import DOWNLOAD_OPERATION, STOP_AND_WAIT
from lib.utils.segments import InitSegment


@dataclass
class ConnectionInfo:
    is_download: bool  # True for download (1), False for upload (2)
    protocol: str     # "sw" for Stop & Wait, "sr" for Selective Repeat
    file_path: str    # For upload: filename to create,
    # for download: path to file
    protocol_handler: object  # StopAndWait or SelectiveRepeat instance

    def __init__(self, init_segment: 'InitSegment', socket, ip, port):
        self.is_download = init_segment.opcode == DOWNLOAD_OPERATION
        self.file_path = init_segment.name.decode("utf-8")
        if init_segment.protocol == STOP_AND_WAIT:
            self.protocol_handler = StopAndWait(socket, ip, port)
        else:
            self.protocol_handler = None
        # None se reemplaza con SelectiveRepeat(socket, ip, port)
