from ..utils.constants import (DOWNLOAD_OPERATION, STOP_AND_WAIT,
                               UPLOAD_OPERATION, SELECTIVE_REPEAT)
from .download_client import DownloadClient
from .upload_client import UploadClient
from .base_client import TransferConfig
import os


def create_client(operation_type, config):
    """Create and return appropriate client instance based on operation type"""
    if operation_type == DOWNLOAD_OPERATION:
        return DownloadClient(config)
    else:
        return UploadClient(config)


def run(args, operation_type):
    """Create and run appropriate client based on operation
    type and arguments"""
    is_upload_operation = operation_type == UPLOAD_OPERATION

    if operation_type == UPLOAD_OPERATION:
        file = args.name
    else:
        file = args.dst

    if args.verbose:
        print("=== Server Config ===")
        print(f"Verbose      : {args.verbose}")
        print(f"Quiet        : {args.quiet}")
        print(f"Host         : {args.host}")
        print(f"Port         : {args.port}")
        if is_upload_operation:
            print(f"Name         : {file}")
        else:
            print(f"Destination  : {file}")
        print(f"Protocol     : {args.protocol}")

    try:
        # Validate file paths
        if is_upload_operation:
            if not args.src or not os.path.exists(args.src):
                print(f"Source file not found: {args.src}")
                return 1
            if args.verbose:
                print(f"File {args.src} found for upload")
            file_path = args.src
        else:
            file_path = args.dst

        server_address = (args.host, args.port)

        # Create config object
        config = TransferConfig(
            server_address=server_address,
            file_name=file,
            file_path=file_path,
            verbose=args.verbose,
            quiet=args.quiet
        )

        # Create and initialize client
        client = create_client(operation_type, config)

        if args.verbose:
            print("Client succesfully created")

        protocol = STOP_AND_WAIT if args.protocol == 'sw' else SELECTIVE_REPEAT

        # Initialize connection
        if not client.init_connection(protocol, args.verbose,
                                      args.quiet):
            print("Connection failed")
            if not args.quiet:
                print(f"Error: {client.error}")
            return 1

        if not args.quiet:
            print("Starting transfer")

        # Start transfer
        success, error = client.start_transfer()

        if not success:
            print("Transfer failed, shut down")
            if not args.quiet:
                print(f"Error: {error}")
        
        elif not args.quiet:
            print("Successfully transferred file")

        return 0 if success else 1

    except Exception as e:
        if not args.quiet:
            print(f"Error: {e}")
        return 1
