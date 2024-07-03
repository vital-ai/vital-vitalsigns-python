

class VitalBlockFile:
    def __init__(self, file_path):
        if not (file_path.endswith('.vital') or file_path.endswith('.vital.bz2')):
            raise ValueError("File must end with either .vital or .vital.bz2")
        self.file_path = file_path
