import socket
import sys
import threading
from typing import Dict, Tuple

from lib.utils.constants import BUFFER_SIZE, DOWNLOAD_OPERATION
# from protocols.stop_and_wait import StopAndWait
# TODO: Import when implemented
# from protocols.selective_repeat import SelectiveRepeat
from ..utils.segments import InitSegment
from ..utils.connection_info import ConnectionInfo


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
                    client_connections[
                        client_address].operation_handler.close_file_manager()
                    del client_connections[client_address]
            return

        # print("previous to client_connections lock")
        # Check if this is a new client (INIT message)

            # print("inside client_connections lock")
        if client_address not in client_connections:
            with client_connections_lock:
                init_segment = InitSegment.deserialize(data, args.verbose)
                client_opcode = init_segment.opcode

                if args.verbose:
                    print("Successfully deserialized init segment")

                connectionInfo = ConnectionInfo(init_segment, server_socket,
                                                client_address, args)
                connectionInfo.lock = threading.Lock()
                client_connections[client_address] = connectionInfo

                init_ack = InitSegment(client_opcode,
                                       init_segment.protocol, 0b1, "")

                init_ack_bytes = init_ack.serialize(args.verbose)

                if not args.quiet:
                    print("Sending INIT_ACK")

                if args.verbose:
                    print(f"INIT_ACK bytes: {init_ack_bytes}")
                # Send INIT_ACK for successful INIT
                server_socket.sendto(init_ack_bytes, client_address)

                needs_initial_upload = client_opcode == DOWNLOAD_OPERATION

                # Needed initiation for server upload operation
            if needs_initial_upload:
                connectionInfo.operation_handler.transfer(is_client=False)
        else:
            connectionInfo = client_connections[client_address]
            connectionInfo.operation_handler.protocol_handler.put_bytes(data)

            protocol = connectionInfo.operation_handler.protocol_handler
            while protocol.waiting_ack:
                continue

            with connectionInfo.lock:
                if args.verbose:
                    print("Is existing client")
                if connectionInfo.finished:
                    print("Already finished transfer with client")
                    return

                finished = connectionInfo.operation_handler.transfer(
                    is_client=False)
                connectionInfo.set_finished(finished)
        # print("release client_connections lock")

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
