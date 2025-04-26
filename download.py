import argparse
from lib.client import download


def main():
    parser = argparse.ArgumentParser(
        prog="download",
        usage="download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] "
        "[-n FILENAME] [-r protocol]",
        description="Download a file placed in FILEPATH on the server running"
        " in ADDR:PORT and save it as FILENAME",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    download.add_arguments(parser)
    args = parser.parse_args()
    download.run(args)


if __name__ == "__main__":
    main()
