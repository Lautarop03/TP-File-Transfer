import argparse
from lib.client.client_manager import run
from lib.client.downloader import Downloader


def add_arguments(parser):
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v", "--verbose", action="store_true",
        help="increase output verbosity",
    )
    verbosity.add_argument(
        "-q", "--quiet", action="store_true",
        help="decrease output verbosity",
    )
    parser.add_argument(
        "-H", "--host", type=str, required=False,
        metavar="", help="server IP address"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=5000,
        metavar="", help="server port"
    )
    parser.add_argument(
        "-n", "--name", type=str, required=False,
        metavar="", help="file name"
    )
    parser.add_argument(
        "-d", "--dst", type=str, required=False,
        metavar="", help="destination file path"
    )
    parser.add_argument(
        "-r", "--protocol", type=str, choices=["sw", "sr"],
        default="sw", required=False,
        metavar="", help="error recovery protocol",
    )


def main():
    parser = argparse.ArgumentParser(
        prog="download",
        usage="download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH]"
        " [-n FILENAME] [-r protocol]",
        description="Download a file named FILENAME on the server running"
        " in ADDR:PORT and save it on FILEPATH",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    add_arguments(parser)
    args = parser.parse_args()

    if args.verbose:
        print("=== Server Config ===")
        print(f"Verbose      : {args.verbose}")
        print(f"Quiet        : {args.quiet}")
        print(f"Host         : {args.host}")
        print(f"Port         : {args.port}")
        print(f"Destination  : {args.dst}")
        print(f"Protocol     : {args.protocol}")

    return run(Downloader(args, is_client=True))


if __name__ == "__main__":
    exit(main())
