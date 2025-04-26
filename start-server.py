import argparse
from lib.server import start_server


def main():
    parser = argparse.ArgumentParser(
        prog='start-server',
        usage='start-server [-h] [-v | -q] [-H ADDR] '
                '[-p PORT] [-s DIRPATH] [-r protocol]',
        description='Start the UDP file transfer server',
        formatter_class=argparse.RawTextHelpFormatter
    )
    start_server.add_arguments(parser)
    args = parser.parse_args()
    start_server.run(args)


if __name__ == '__main__':
    main()
