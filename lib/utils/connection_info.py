from dataclasses import dataclass


@dataclass
class ConnectionInfo:
    is_download: bool  # True for download (1), False for upload (2)
    protocol: str     # "sw" for Stop & Wait, "sr" for Selective Repeat
    file_path: str    # For upload: filename to create,
    # for download: path to file
    protocol_handler: object  # StopAndWait or SelectiveRepeat instance
