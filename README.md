# TP File Transfer

Repositorio para el TP1 de Redes del Grupo 10

## Server

Para iniciar el servidor:

```sh
~$ python start-server.py -h
usage: start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH] [-r protocol]

Start the UDP file transfer server, will listen on ADDR:PORT

options:
  -h, --help        show this help message and exit
  -v, --verbose     increase output verbosity
  -q, --quiet       decrease output verbosity
  -H , --host       service IP address
  -p , --port       service port
  -s , --storage    storage dir path
  -r , --protocol   error recovery protocol
```

### Ejemplo

```sh
python3 start-server.py -H 127.0.0.1 -p 1234 -s ./files/server -r sw
```

## Client - Upload

Para subir un archivo al servidor:

```sh
~$ python3 upload.py -h
usage: upload [-h] [-v | -q] [-H ADDR] [-p PORT] [-s FILEPATH] [-n FILENAME] [-r protocol]

Upload the file located in FILEPATH to the server running on ADDR:PORT, will be saved as FILENAME

options:
  -h, --help        show this help message and exit
  -v, --verbose     increase output verbosity
  -q, --quiet       decrease output verbosity
  -H , --host       server IP address
  -p , --port       server port
  -n , --name       file name
  -s , --src        source file path
  -r , --protocol   error recovery protocol
```

### Ejemplo

```sh
python3 upload.py -H 127.0.0.1 -p 1234 -s ./files/client/5.png -n upload5.png -r sw
```

## Client - Download

Para descargar un archivo del servidor:

```sh
~$ python3 download.py -h
usage: download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME] [-r protocol]

Download a file named FILENAME on the server running in ADDR:PORT and save it on FILEPATH

options:
  -h, --help        show this help message and exit
  -v, --verbose     increase output verbosity
  -q, --quiet       decrease output verbosity
  -H , --host       server IP address
  -p , --port       server port
  -n , --name       file name
  -d , --dst        destination file path
  -r , --protocol   error recovery protocol
```

### Ejemplo

```sh
python3 download.py -v -H 127.0.0.1 -p 1234 -d ./files/client/dlorem5.txt -n lorem5.txt -r sw
```
