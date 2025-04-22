from constants import BUFFER_SIZE
import os


class FileManager:
    def __init__(self, path, mode):
        self.path = path
        self.mode = mode
        self.file = None

    def open(self):
        try:
            self.file = open(self.path, self.mode)
        except OSError as e:
            print(f"Error al abrir el archivo: {e}")
            self.file = None

    def read(self):
        if self.file and "rb" in self.mode:
            try:
                return self.file.read(BUFFER_SIZE)
            except Exception as e:
                print(f"Error al leer el archivo: {e}")
        else:
            print("Archivo no abierto en modo lectura binaria.")
        return None

    def write(self, data):
        if self.file and ("wb" in self.mode):
            try:
                self.file.write(data)
            except Exception as e:
                print(f"Error al escribir en el archivo: {e}")
        else:
            print("Archivo no abierto en modo escritura binaria.")

    def close(self):
        if self.file:
            try:
                self.file.close()
            except Exception as e:
                print(f"Error al cerrar el archivo: {e}")
            finally:
                self.file = None

    def file_size(self):
        if self.file:
            try:
                return os.path.getsize(self.path)
            except Exception as e:
                print(f"Error al obtener el tamaño del archivo: {e}")
        return None
