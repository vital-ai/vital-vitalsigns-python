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

    def _get_uncompressed_bz2_size(self):
        with bz2.BZ2File(self.file.file_path, 'rb') as f:
            f.seek(0, 2)  # Move the cursor to the end of the file
            return f.tell()

    def _get_file_size(self):
        if self.file.file_path.endswith('.bz2'):
            return self._get_uncompressed_bz2_size()
        else:
            return os.path.getsize(self.file.file_path)

