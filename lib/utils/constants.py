BUFFER_SIZE = 1400  # Buffer size for receiving/sending data

HEADER_SIZE_SW = 7  # Packet header size, 1 flags, 2 length payload, 4 checksum

HEADER_SIZE_SR = 13

DATA_SIZE = BUFFER_SIZE - HEADER_SIZE_SW  # Maximum packet data size

TIMEOUT = 0.1  # Timeout to receive an ACK

APPEND_MODE = "ab"  # Append mode for binary files

WRITE_MODE = "wb"  # Write mode for binary files

READ_MODE = "rb"  # Read mode for binary files

EOF_MARKER = object()

MAX_ATTEMPTS = 10  # Maximum sending attempts

# Operation Types
DOWNLOAD_OPERATION = 0b0
UPLOAD_OPERATION = 0b1

# Protocol Types
STOP_AND_WAIT = 0b0
SELECTIVE_REPEAT = 0b1
