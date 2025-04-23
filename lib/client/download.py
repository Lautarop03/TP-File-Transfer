def add_arguments(parser):
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="increase output verbosity",
    )
    verbosity.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=True,
        help="decrease output verbosity",
    )

    parser.add_argument(
        "-H", "--host", type=str, required=False, metavar="", help="server IP address"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=5000, metavar="", help="server port"
    )
    parser.add_argument(
        "-d",
        "--dst",
        type=str,
        required=False,
        metavar="",
        help="destination file path",
    )
    parser.add_argument(
        "-n", "--name", type=str, required=False, metavar="", help="file name"
    )
    parser.add_argument(
        "-r",
        "--protocol",
        type=str,
        choices=["sw", "sr"],
        default="sw",
        required=False,
        metavar="",
        help="error recovery protocol",
    )


def run(args):
    if args.verbose:
        print("=== Download Config ===")
        print(f"Verbose      : {args.verbose}")
        print(f"Quiet        : {args.quiet}")
        print(f"Host         : {args.host}")
        print(f"Port         : {args.port}")
        print(f"Destination  : {args.dst}")
        print(f"File Name    : {args.name}")
        print(f"Protocol     : {args.protocol}")
