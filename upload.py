import argparse
from lib.client import upload

def main():
    parser = argparse.ArgumentParser(
        prog='upload',
        usage='upload [-h] [-v | -q] [-H ADDR] [-p PORT] [-s FILEPATH] [-n FILENAME] [-r protocol]',
        description='Upload the file located in FILEPATH to the server running on ADDR:PORT, will be saved as FILENAME',
        formatter_class=argparse.RawTextHelpFormatter
    )
    upload.add_arguments(parser)
    args = parser.parse_args()
    upload.run(args)

if __name__ == '__main__':
    main()