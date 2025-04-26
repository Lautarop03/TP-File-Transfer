import argparse
from lib.client.client_manager import run
from lib.utils.constants import DOWNLOAD_OPERATION


def add_arguments(parser):
    parser.add_argument(
        "-n", "--name", type=str, required=False,
        metavar="", help="file name"
    )
    parser.add_argument(
        "-d", "--dst", type=str, required=False,
        metavar="", help="destination file path"
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
        "-r", "--protocol", type=str, choices=["sw", "sr"],
        default="sw", required=False,
        metavar="", help="error recovery protocol",
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v", "--verbose", action="store_true",
        default=False, help="increase output verbosity",
    )
    verbosity.add_argument(
        "-q", "--quiet", action="store_true",
        default=True, help="decrease output verbosity",
    )


def main():
    parser = argparse.ArgumentParser(
        prog="download",
        usage="download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH]"
        " [-n FILENAME] [-r protocol]",
        description="Download a file placed in FILEPATH on the server running"
        " in ADDR:PORT and save it as FILENAME",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    add_arguments(parser)
    args = parser.parse_args()
    return run(args, DOWNLOAD_OPERATION)


if __name__ == "__main__":
    exit(main())
