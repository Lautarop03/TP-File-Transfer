from dataclasses import dataclass


@dataclass
class TransferConfig:
    server_address: tuple[str, int]
    file_name: str
    file_path: str
    verbose: bool = False
    quiet: bool = False
