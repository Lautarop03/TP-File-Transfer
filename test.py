import socket


def main():

    # Server address and port
    server_address = ('127.0.0.1', 1234)

    # Data to send (as bytes)
    data = b'\x01\x02\x03\x04Hello, server!\x05\x06'

    # Create a UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        print(f"Sending data to {server_address}")
        sock.sendto(data, server_address)
        print("Data sent.")


main()
