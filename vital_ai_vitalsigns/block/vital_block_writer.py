from typing import List
from vital_ai_vitalsigns.block.vital_block_io import VitalBlockIO

class VitalBlockWriter(VitalBlockIO):
    def __init__(self, file, *, encoding="jsonl", version="1.0.0", ontologies: List[dict] = [], metadata: dict = {}):
        if not (file.file_path.endswith('.vital') or file.file_path.endswith('.vital.bz2')):
            raise ValueError("File must end with either .vital or .vital.bz2")
        super().__init__(file)
        self.file_handle = self._open_file('wt')
        self.closed = False
        self.header_written = False
        self.encoding = encoding
        self.version = version
        self.ontologies = ontologies
        self.metadata = metadata

    def write_header(self):
        if self.closed:
            raise RuntimeError("Cannot write to a closed file.")
        self.file_handle.write(f"{self.encoding} {self.version}\n")
        for ontology in self.ontologies:
            self.file_handle.write(f"@{ontology['iri']} {ontology['version']}\n")
        for key, value in self.metadata.items():
            self.file_handle.write(f"{key}: {value}\n")
        self.file_handle.write("|\n")
        self.header_written = True

    def write_block(self, block):
        if self.closed:
            raise RuntimeError("Cannot write to a closed file.")
        if not self.header_written:
            raise RuntimeError("Header must be written before writing blocks.")
        self.file_handle.write("|\n")
        for obj in block.objects:
            json_str = obj.to_json(pretty_print=False)
            self.file_handle.write(f"{json_str}\n")

    def close(self):
        if not self.closed:
            self.file_handle.write("|\n")  # Optionally add a zero-object block before EOF
            self.file_handle.close()
            self.closed = True

    def __del__(self):
        self.close()

