from dataclasses import dataclass

from lib.client.downloader import Downloader
from lib.client.uploader import Uploader
from lib.protocols.stop_and_wait import StopAndWait
from lib.protocols.selective_repeat import SelectiveRepeat
from lib.utils.constants import DOWNLOAD_OPERATION, STOP_AND_WAIT
from lib.utils.segments import InitSegment


@dataclass
class ConnectionInfo:
    operation_handler: object  # Downloader or Uploader
    protocol: str     # "sw" for Stop & Wait, "sr" for Selective Repeat
    file_path: str    # For upload: filename to create,
    protocol_handler: object  # StopAndWait or SelectiveRepeat instance

    # def __init__(self, init_segment: 'InitSegment', socket, ip, port,
    #              verbose, quiet):
    def __init__(self, init_segment: 'InitSegment',
                 socket, client_address, args):

        if init_segment.opcode == DOWNLOAD_OPERATION:
            args.dst = init_segment.name
            operation_handler = Uploader(args)
        else:
            args.name = init_segment.name
            args.dst = args.storage + '/' + init_segment.name.decode("utf-8")
            args.host = client_address[0]
            args.port = client_address[1]
            operation_handler = Downloader(args, False)

        self.operation_handler = operation_handler
        self.file_path = init_segment.name.decode("utf-8")
        if init_segment.protocol == STOP_AND_WAIT:
            self.protocol_handler = StopAndWait(socket, client_address,
                                                args.verbose, args.quiet)
        else:
            self.protocol_handler = SelectiveRepeat(socket, client_address,
                                                    args.verbose, args.quiet)
