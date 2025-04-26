BUFFER_SIZE = 1024  # Tamaño del buffer para recibir/enviar datos
HEADER_SIZE = (
    7  # Tamaño del encabezado del paquete, 1 flags,
    # 2 lenght payload, 4 checksum
)
DATA_SIZE = BUFFER_SIZE - HEADER_SIZE  # Tamaño máximo de los datos del paquete

TIMEOUT = 0.5  # Tiempo de espera para recibir un ACK

WRITE_MODE = "wb"  # Modo de escritura para archivos binarios

READ_MODE = "rb"  # Modo de lectura para archivos binarios

MAX_ATTEMPTS = 10  # Maximo de intentos de envio

# Operation types
DOWNLOAD_OPERATION = 1
UPLOAD_OPERATION = 2
