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


def handle_client_connection(args, data: bytes,
                             client_address: Tuple[str, int],
                             conn_info: ConnectionInfo) -> bool:
    """Handle the file transfer for a client in a separate thread"""
    try:
        if conn_info.is_download:
            conn_info.protocol_handler.send_file(conn_info.file_path)
        else:
            conn_info.protocol_handler.receive_file(
                data, args.storage + '/' + conn_info.file_path)
    except Exception as e:
        print(
            f"Error on {'download' if conn_info.is_download else 'upload'}"
            f" for {client_address}: {e}")


def process_message(data: bytes, client_address: Tuple[str, int],
                    server_socket: socket.socket,
                    client_connections: Dict[Tuple[str, int], ConnectionInfo],
                    args):
    """Handle received message in a separate thread"""
    try:
        if not args.quiet:
            print(f"Processing data from {client_address}")
            print(f"Data length: {len(data)} bytes")

        if args.verbose:
            print(f"data: {data}")

        # Check if this is a FIN message
        if data == b"FIN":
            if not args.quiet:
                print(f"Received FIN message from {client_address}")
            # Remove client from connections
            with client_connections_lock:
                if client_address in client_connections:
                    client_connection = client_connections[client_address]
                    client_connection.protocol_handler.socket.close()
                    del client_connections[client_address]
            return

        # Check if this is a new client (INIT message)
        with client_connections_lock:
            if client_address not in client_connections:
                init_segment = InitSegment.deserialize(data, args.verbose)

                if args.verbose:
                    print("Successfully deserialized init segment")

                connectionInfo = ConnectionInfo(init_segment, server_socket,
                                                client_address, args)

                client_connections[client_address] = connectionInfo

                init_ack = InitSegment(init_segment.opcode,
                                       init_segment.protocol, 0b1, "")

                init_ack_bytes = init_ack.serialize(args.verbose)

                if not args.quiet:
                    print("Sending INIT_ACK")

                if args.verbose:
                    print(f"INIT_ACK bytes: {init_ack_bytes}")
                # Send INIT_ACK for successful INIT
                server_socket.sendto(init_ack_bytes, client_address)
            else:
                # entity opuesto a la op
                if args.verbose:
                    print("Is existing client")
                client_connections[client_address].operation_handler.transfer(
                    data)

                # handle_client_connection(args, data, client_address,
                #                          client_connections[client_address])
                # If not an INIT message, let the protocol handler handle it
                # client_info = client_connections[client_address]
                # client_info.protocol_handler.receive_file(
                #     args.storage + '/' + client_info.file_path)

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

    server_socket.settimeout(5.0)  # 5 segundos

    try:
        # Bind socket to address
        server_socket.bind((args.host, args.port))
        print(f"\nServer started. Listening on {args.host}:{args.port}")

        flag = 1
        while True:
            try:
                # Receive data
                data, client_address = server_socket.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                if not args.quiet:
                    print("[SERVER] Waiting for any client message...")
                continue

            if not args.quiet:
                print(f"\n[MSG N°{flag}] Received data from client:"
                      f"{client_address}")
            flag += 1

            # Create and start a new thread for message processing
            thread = threading.Thread(
                target=process_message,
                args=(data, client_address, server_socket,
                      client_connections, args)
            )
            thread.daemon = True
            thread.start()

    except KeyboardInterrupt:
        print("\nServer shutting down by keyboard interrupt...")
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        raise e

    finally:
        server_socket.close()
