import argparse
from lib.server import server_manager


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
        "-H", "--host", type=str, default="0.0.0.0",
        metavar="", help="service IP address",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=5000,
        metavar="", help="service port"
    )
    parser.add_argument(
        "-s", "--storage", type=str, default="files/server/", required=False,
        metavar="", help="storage dir path",
    )
    parser.add_argument(
        "-r", "--protocol", type=str, choices=["sw", "sr"],
        default="sw", metavar="", help="error recovery protocol",
    )


def main():
    parser = argparse.ArgumentParser(
        prog='start-server',
        usage='start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]'
        ' [-r protocol]',
        description='Start the UDP file transfer server, will listen'
        ' on ADDR:PORT',
        formatter_class=argparse.RawTextHelpFormatter
    )
    add_arguments(parser)
    args = parser.parse_args()
    server_manager.run(args)


if __name__ == '__main__':
    main()
