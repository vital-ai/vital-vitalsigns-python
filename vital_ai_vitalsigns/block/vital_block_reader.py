import json
from vital_ai_vitalsigns.block.vital_block import VitalBlock
from vital_ai_vitalsigns.block.vital_block_io import VitalBlockIO

class VitalBlockReader(VitalBlockIO):
    acceptable_versions = {'1.0.0'}

    def __init__(self, file, *, triples_only=False):
        super().__init__(file)
        self.started_reading = False
        self.encoding = None
        self.version = None
        self.ontologies = []
        self.metadata = {}
        self.triples_only = triples_only
        self._read_header()

    def _read_header(self):
        with self._open_file('rt') as file:
            first_line = file.readline().strip()
            self.encoding, self.version = first_line.split()
            if self.encoding != 'jsonl':
                raise ValueError("Only 'jsonl' encoding is supported")
            if self.version not in self.acceptable_versions:
                raise ValueError(f"Unsupported version: {self.version}")

            for line in file:
                stripped_line = line.strip()
                if stripped_line == '|':
                    break
                elif stripped_line.startswith('@'):
                    iri, version = stripped_line[1:].split(maxsplit=1)
                    self.ontologies.append({'iri': iri, 'version': version})
                else:
                    key, value = stripped_line.split(':', 1)
                    self.metadata[key.strip()] = value.strip()

    def get_encoding(self):
        return self.encoding

    def get_version(self):
        return self.version

    def get_ontologies(self):
        return self.ontologies

    def get_metadata(self):
        return self.metadata

    def __iter__(self):
        if self.started_reading:
            raise RuntimeError("Cannot create parallel readers after reading has started.")
        self.started_reading = True

        current_block = []

        with self._open_file('rt') as file:

            after_header = False

            for line in file:

                stripped_line = line.strip()

                if stripped_line.startswith('#'):
                    continue  # Skip comment lines

                if not after_header:
                    if stripped_line == '|':
                        after_header = True
                    else:
                        continue

                if stripped_line == '|':
                    if current_block:
                        yield VitalBlock(current_block)
                        current_block = []
                else:
                    try:
                        # json_obj = json.loads(stripped_line)
                        # go = GraphObject.from_json(stripped_line)
                        current_block.append(stripped_line)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Failed to parse JSON: {stripped_line}") from e
            if current_block:
                yield VitalBlock(current_block)  # Yield the last block if any

    def get_parallel_readers(self, n):

        from vital_ai_vitalsigns.block.vital_block_parallel_reader import VitalBlockParallelReader

        if self.started_reading:
            raise RuntimeError("Cannot create parallel readers after reading has started.")
        file_size = self._get_file_size()
        positions = self._calculate_positions(file_size, n)
        unique_positions = self._find_unique_positions(positions)
        parallel_list = [VitalBlockParallelReader(self.file, start, end, num, triples_only=self.triples_only) for num, (start, end) in enumerate(unique_positions)]
        first_reader = parallel_list[0]
        first_reader.first = True
        return parallel_list

    def _calculate_positions(self, file_size, n):
        block_size = file_size // n
        positions = [(i * block_size, (i + 1) * block_size) for i in range(n)]
        return positions

    def _find_unique_positions(self, positions):
        unique_positions = []
        seen_blocks = set()

        with self._open_file('rb') as file:

            for start, end in positions:
                file.seek(start)
                self._skip_to_next_block(file)
                start_pos = file.tell()

                seen_blocks.add(start_pos)

                file.seek(end)

                self._skip_to_next_block(file)

                end_pos = file.tell()

                unique_positions.append((start_pos, end_pos))

        return unique_positions

    def _skip_to_next_block(self, file):
        while True:
            line = file.readline()
            if not line:
                break
            if line.strip() == b'|':
                break

