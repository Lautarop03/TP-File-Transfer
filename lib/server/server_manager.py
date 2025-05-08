import socket
import sys
import threading
from typing import Dict, Tuple

from lib.utils.constants import BUFFER_SIZE, DOWNLOAD_OPERATION
from ..utils.segments import InitSegment
from ..utils.connection_info import ConnectionInfo


def process_message(data: bytes, client_address: Tuple[str, int],
                    server_socket: socket.socket,
                    client_connections: Dict[Tuple[str, int], ConnectionInfo],
                    args):
    """Handle received message in a separate thread"""
    try:
        if not args.quiet:
            print(f"[SERVER] Processing {len(data)} bytes of data "
                  f"from {client_address}")

        # Check if this is a FIN message
        if data == b"FIN":
            print(f"[SERVER] Received FIN message from {client_address}")
            # Remove client from connections
            with client_connections_lock:
                if client_address in client_connections:
                    client_connections[
                        client_address].terminate()
                    del client_connections[client_address]
            return

        # Check if this is a new client (INIT message)
        if client_address not in client_connections:
            with client_connections_lock:
                print("[SERVER] Starting new connection "
                      f"with {client_address}")
                init_segment = InitSegment.deserialize(data, args.verbose)
                client_opcode = init_segment.opcode

                if args.verbose:
                    print("[SERVER] Successfully deserialized init segment "
                          f"from {client_address}")

                connectionInfo = ConnectionInfo(init_segment,
                                                client_address, args)
                connectionInfo.lock = threading.Lock()
                client_connections[client_address] = connectionInfo

                init_ack = InitSegment(client_opcode,
                                       init_segment.protocol, 0b1, "")

                init_ack_bytes = init_ack.serialize(args.verbose)

                if not args.quiet:
                    print("[SERVER] Sending connection confirmation "
                          f"with {client_address}")

                if args.verbose:
                    print(f"[SERVER] Sending INIT_ACK bytes: {init_ack_bytes}")
                # Send INIT_ACK for successful INIT
                server_socket.sendto(init_ack_bytes, client_address)

                needs_initial_upload = client_opcode == DOWNLOAD_OPERATION

                # Needed initiation for server upload operation
            with client_connections[client_address].lock:
                if needs_initial_upload:
                    connectionInfo.operation_handler.transfer(is_client=False)
        else:
            connectionInfo = client_connections[client_address]
            connectionInfo.operation_handler.protocol_handler.put_bytes(data)

            with connectionInfo.lock:
                if args.verbose:
                    print(f"[SERVER] Is existing client: {client_address}")
                if connectionInfo.finished:
                    print("[SERVER] Already finished transfer "
                          f"with {client_address}")
                    return

                finished = connectionInfo.operation_handler.transfer(
                    is_client=False)
                connectionInfo.set_finished(finished)

    except Exception as e:
        if args.verbose:
            print("[SERVER] Error processing message "
                  f"from {client_address}: {e}")
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
                print(f"\n[SERVER]-[MSG N°{flag}] Received data from client: "
                      f"{client_address}\n")
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
        print("\nServer shutting down gracefully\n")
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        raise e

    finally:
        server_socket.close()
