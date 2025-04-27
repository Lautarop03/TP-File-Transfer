from constants import DATA_SIZE
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
            print(f"Error opening file: {e}")
            self.file = None

    def read(self):
        if self.file and "rb" in self.mode:
            try:
                return self.file.read(DATA_SIZE)
            except Exception as e:
                print(f"Error reading file: {e}")
        else:
            print("File not opened in binary read mode.")
        return None

    def write(self, data):
        if self.file and ("wb" in self.mode):
            try:
                self.file.write(data)
            except Exception as e:
                print(f"Error writing to file: {e}")
        else:
            print("File not opened in binary write mode.")

    def close(self):
        if self.file:
            try:
                self.file.close()
            except Exception as e:
                print(f"Error closing file: {e}")
            finally:
                self.file = None

    def file_size(self):
        if self.file:
            try:
                return os.path.getsize(self.path)
            except Exception as e:
                print(f"Error getting file size: {e}")
        return None
