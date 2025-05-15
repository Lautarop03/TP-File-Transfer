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

Aclaración: Asumimos que ```FILENAME``` es el nombre del archivo a buscar en el servidor y que ```FILEPATH``` es el path local del cliente donde se va a guardar el archivo a descargar del servidor, por ello esta varible o path debe terminar con el nombre con que se guardara el archivo.

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

## Mininet - Topología con pérdida de paquetes

Pre: Instalar mininet y xterm por terminal

Iniciar la topoligía con una cantidad de hosts y una tasa de pérdida de paquetes (El ```server``` se crea por default):

```sh
usage: topo_mn.py [-h] [-nh N_HOSTS] [-lr LOSS_RATE]

sudo python3 topo_mn.py -nh 2 -lr 5
```

### Ejemplo de uso:

1) Iniciar topoligía con mininet
    ```sh
    sudo python3 topo_mn.py -nh 2 -lr 5
    ```

2) Iniciar el servidor en la terminal ```host:server```:
    ```sh
    python3 start-server.py -H 10.0.0.1 -p 1234 -s ./files/server -r sw
    ```

3) Iniciar los clientes en la terminal ```host:h0``` y ```host:h1``` en simultaneo

    En ```host:h0```:
    ```sh
    python3 upload.py -H 10.0.0.1 -p 1234 -s ./files/client/5.png -n upload5.png -r sw
    ```

    En ```host:h1```:

    ```sh
    python3 download.py -H 10.0.0.1 -p 1234 -d ./files/client/dlorem5.txt -n lorem5.txt -r sw
    ```

4) (Opcional) Verificar si dos archivos son idénticos en contenido mediante su hash
    
    Por consola ejecutar lo siguiente, imprime ```Iguales``` o ```Distintos``` segun corresponda

    - Para comparar el archivo subido:
      ```sh
      if [ "$(sha256sum files/client/5.png | awk '{print $1}')" = "$(sha256sum upload5.png | awk '{print $1}')" ]; then
        echo "Iguales"
      else
        echo "Distintos"
      fi
      ```
    
    - Para comparar el archivo descargado:
      ```sh
      if [ "$(sha256sum files/server/loremt.txt | awk '{print $1}')" = "$(sha256sum dlorem5.txt | awk '{print $1}')" ]; then
        echo "Iguales"
      else
        echo "Distintos"
      fi
      ```
