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
        "-H",
        "--host",
        type=str,
        default="0.0.0.0",
        metavar="",
        help="service IP address",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=5000, metavar="", help="service port"
    )
    parser.add_argument(
        "-s",
        "--storage",
        type=str,
        default="/",
        required=False,
        metavar="",
        help="storage dir path",
    )
    parser.add_argument(
        "-r",
        "--protocol",
        type=str,
        choices=["sw", "sr"],
        default="sw",
        metavar="",
        help="error recovery protocol",
    )


def run(args):
    if args.verbose:
        print("=== Server Config ===")
        print(f"Verbose      : {args.verbose}")
        print(f"Quiet        : {args.quiet}")
        print(f"Host         : {args.host}")
        print(f"Port         : {args.port}")
        print(f"Storage Path : {args.storage}")
        print(f"Protocol     : {args.protocol}")
