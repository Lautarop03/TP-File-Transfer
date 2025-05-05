from lib.utils.segments import InitSegment
from ..utils.constants import BUFFER_SIZE


def run(operation):
    """Create and run appropriate client based on operation
    type and arguments"""

    try:
        # Initialize connection
        if not init_connection(operation):
            print("Connection failed")
            if not operation.quiet:
                print(f"Error: {operation.error}")
            return 1

        if not operation.quiet:
            print("\nStarting transfer")

        # if operation.is_download:
        #     is_finished = False
        #     # Start transfer
        #     while not is_finished:
        #         data, _ = operation.socket.recvfrom(BUFFER_SIZE)
        #         # Start transfer
        #         is_finished = operation.transfer(data)
        # else:
        #     operation.transfer("")

        operation.transfer(is_client=True)

        # if not success:
        #     print("Transfer failed, shut down")
        #     if not operation.quiet:
        #         print(f"Error: {error}")

        # elif not operation.quiet:
        #     print("Successfully transferred file")

        # return 0 if success else 1

        return 0

    except Exception as e:
        if not operation.quiet:
            print(f"Error: {e}")
        return 1


def init_connection(operation) -> bool:
    """Initialize connection with server"""
    try:
        if not operation.quiet:
            print("Initiating connection with server")

        # Create and send INIT message
        init_segment = InitSegment(operation.op_code, operation.protocol_code,
                                   0b0, operation.file_name)

        init_message = init_segment.serialize(operation.verbose)

        if operation.verbose:
            print(f"Created init message with data: {init_message}")
            print("Trying to connect with server running on "
                  f"{operation.destination_address[0]}:"
                  f"{operation.destination_address[1]}")

        operation.socket.sendto(
            init_message, operation.destination_address)

        if not operation.quiet:
            print("Waiting for server response")

        # Wait for server response
        operation.socket.settimeout(5)  # 5 seconds timeout for INIT response
        response, _ = operation.socket.recvfrom(BUFFER_SIZE)

        if not operation.quiet:
            print("Received server response")

        if operation.verbose:
            print(f"Received bytes: {response}")

        init_segment = InitSegment.deserialize(response, operation.verbose)
        if not init_segment.ack == 0b1:
            operation.error = "Response from server is not ACK"
            return False

        return True

    except Exception as e:
        operation.error = f"Connection initialization failed: {str(e)}"
        return False
