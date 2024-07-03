import json
from vital_ai_vitalsigns.block.vital_block import VitalBlock
from vital_ai_vitalsigns.block.vital_block_reader import VitalBlockReader


class VitalBlockParallelReader(VitalBlockReader):
    def __init__(self, file, start, end):
        super().__init__(file)
        self.start = start
        self.end = end
        self.started_reading = True  # Ensure parallel readers don't create further readers

    def __iter__(self):
        current_block = []
        with self._open_file('rt') as file:
            file.seek(self.start)
            while file.tell() < self.end:
                line = file.readline()
                if not line:
                    break
                stripped_line = line.strip()
                if stripped_line.startswith('#'):
                    continue  # Skip comment lines
                elif stripped_line == '|':
                    if current_block:
                        yield VitalBlock(current_block)
                        current_block = []
                else:
                    try:
                        json_obj = json.loads(stripped_line)
                        current_block.append(json_obj)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Failed to parse JSON: {stripped_line}") from e
            if current_block:
                yield VitalBlock(current_block)  # Yield the last block if any

