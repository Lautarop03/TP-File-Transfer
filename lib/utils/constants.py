BUFFER_SIZE = 1024  # Buffer size for receiving/sending data
HEADER_SIZE = (
    7  # Packet header size, 1 flags, 2 length payload, 4 checksum
)
DATA_SIZE = BUFFER_SIZE - HEADER_SIZE  # Maximum packet data size

TIMEOUT = 0.5  # Timeout to receive an ACK

WRITE_MODE = "wb"  # Write mode for binary files

READ_MODE = "rb"  # Read mode for binary files

MAX_ATTEMPTS = 10  # Maximum sending attempts
