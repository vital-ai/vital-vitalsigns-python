import bz2
import os


class VitalBlockIO:
    def __init__(self, file):
        self.file = file

    def _open_file(self, mode):
        if self.file.file_path.endswith('.bz2'):
            return bz2.open(self.file.file_path, mode)
        else:
            return open(self.file.file_path, mode)

    def _get_file_size(self):
        return os.path.getsize(self.file.file_path)
