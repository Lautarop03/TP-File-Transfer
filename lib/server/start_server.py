import socket
import sys
import threading
from typing import Dict, Tuple

from lib.utils.constants import BUFFER_SIZE
# from protocols.stop_and_wait import StopAndWait
# TODO: Import when implemented
# from protocols.selective_repeat import SelectiveRepeat
from ..utils.segments import InitSegment
from ..utils.connection_info import ConnectionInfo


def handle_client_connection(client_address: Tuple[str, int],
                             conn_info: ConnectionInfo):
    """Handle the file transfer for a client in a separate thread"""
    try:
        if conn_info.is_download:
            conn_info.protocol_handler.send_file(conn_info.file_path)
        else:
            conn_info.protocol_handler.receive_file(conn_info.file_path)
    except Exception as e:
        print(
            f"Error on {'download' if conn_info.is_download else 'upload'}"
            f"for {client_address}: {e}")


def process_message(data: bytes, client_address: Tuple[str, int],
                    server_socket: socket.socket,
                    client_connections: Dict[Tuple[str, int], ConnectionInfo],
                    args):
    """Handle received message in a separate thread"""
    try:
        if args.verbose:
            print(f"\nProcessing data from {client_address}")
            print(f"Data length: {len(data)} bytes")

        # Check if this is a new client (INIT message)
        with client_connections_lock:
            if client_address not in client_connections:
                init_segment = InitSegment.deserialize(data)

                connectionInfo = ConnectionInfo(init_segment)

                client_connections[client_address] = connectionInfo

                init_ack = InitSegment(init_segment.opcode,
                                       init_segment.protocol, 0b1, "")

                init_ack_bytes = init_ack.serialize(args.verbose)

                # Send INIT_ACK for successful INIT
                server_socket.sendto(init_ack_bytes, client_address)

                # Start a new thread to handle the file transfer
                transfer_thread = threading.Thread(
                    target=handle_client_connection,
                    args=(client_address, connectionInfo)
                )
                transfer_thread.daemon = True
                transfer_thread.start()
                return

            # If not an INIT message, let the protocol handler handle it
            client_connections[client_address].protocol_handler.receive()

    except Exception as e:
        if args.verbose:
            print(f"Error processing message from {client_address}: {e}")
        server_socket.sendto(
            "ERROR: Internal server error".encode(),
            client_address)


def run(args):
    if args.verbose:
        print("=== Server Config ===")
        print(f"Verbose      : {args.verbose}")
        print(f"Quiet        : {args.quiet}")
        print(f"Host         : {args.host}")
        print(f"Port         : {args.port}")
        print(f"Storage Path : {args.storage}")
        print(f"Protocol     : {args.protocol}")

    # Create UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Dictionary to store client connections
    client_connections: Dict[Tuple[str, int], ConnectionInfo] = {}
    global client_connections_lock
    client_connections_lock = threading.Lock()

    try:
        # Bind socket to address
        server_socket.bind((args.host, args.port))
        if args.verbose:
            print(f"\nServer started. Listening on {args.host}:{args.port}")

        while True:
            # Receive data
            data, client_address = server_socket.recvfrom(BUFFER_SIZE)

            # Create and start a new thread for message processing
            thread = threading.Thread(
                target=process_message,
                args=(data, client_address, server_socket,
                      client_connections, args)
            )
            thread.daemon = True
            thread.start()

    except Exception as e:
        if not args.quiet:
            print(f"Server error: {e}", file=sys.stderr)
        raise e

    finally:
        server_socket.close()
