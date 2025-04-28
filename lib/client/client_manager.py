from utils.constants import DOWNLOAD_OPERATION, UPLOAD_OPERATION
from .download_client import DownloadClient
from .upload_client import UploadClient
from base_client import TransferConfig
import os


def create_client(config):
    """Create and return appropriate client instance based on operation type"""
    if config.operation_type == DOWNLOAD_OPERATION:
        return DownloadClient(config)
    else:
        return UploadClient(config)


def run(args, operation_type):
    """Create and run appropriate client based on operation
    type and arguments"""
    try:
        # Validate file paths
        if operation_type == UPLOAD_OPERATION:
            if not args.src or not os.path.exists(args.src):
                if not args.quiet:
                    print(f"Source file not found: {args.src}")
                return 1

        # Create config object
        config = TransferConfig(
            operation_type=operation_type,
            host=args.host,
            port=args.port,
            protocol=args.protocol,
            # esto al final es un solo path...
            file_path=args.src if operation_type == UPLOAD_OPERATION
            else args.dst,
            file_name=args.name,
            verbose=args.verbose
        )

        # Create and initialize client
        client = create_client(config)

        # Initialize connection
        if not client.init_connection():
            if not args.quiet:
                print(f"Connection failed: {client.error}")
            return 1

        # Start transfer
        success, error = client.start_transfer()

        if not success and not args.quiet:
            print(f"Transfer failed: {error}")

        return 0 if success else 1

    except Exception as e:
        if not args.quiet:
            print(f"Error: {e}")
        return 1
