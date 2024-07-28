import json
from vital_ai_vitalsigns.block.vital_block import VitalBlock
from vital_ai_vitalsigns.block.vital_block_reader import VitalBlockReader
import mmap


class VitalBlockParallelReader(VitalBlockReader):
    def __init__(self, file, start, end, num=0, *, triples_only=False):
        super().__init__(file)
        self.first = False
        self.start = start
        self.end = end
        self.num = num
        self.triples_only = triples_only
        # Ensure parallel readers don't create further readers
        self.started_reading = True

    def __repr__(self):
        size = self.end - self.start
        return f"VitalBlockParallelReader(num={self.num}, size={size}, start={self.start}, end={self.end})"

    def __iter__(self):
        current_block = []

        if self.first:
            after_header = False
        else:
            after_header = True

        with self._open_file('rt') as file:

            mmap_obj = mmap.mmap(file.fileno(), length=0, access=mmap.ACCESS_READ)

            # file.seek(self.start)
            mmap_obj.seek(self.start)

            # while file.tell() < self.end:
            while mmap_obj.tell() < self.end:

                # line = file.readline()
                line = mmap_obj.readline()

                if not line:
                    break

                # stripped_line = line.strip()
                stripped_line = line.strip().decode('utf-8')

                # print(stripped_line)

                if stripped_line.startswith('#'):
                    continue  # Skip comment lines

                if not after_header:
                    if stripped_line == '|':
                        after_header = True
                    else:
                        continue

                if stripped_line == '|':
                    if current_block:
                        # print(f"Yielding Size: {len(current_block)}")
                        yield VitalBlock(current_block, triples_only=self.triples_only)
                        current_block = []
                else:
                    try:
                        # json_obj = json.loads(stripped_line)
                        # current_block.append(json_obj)
                        current_block.append(stripped_line)
                    except json.JSONDecodeError as e:
                        mmap_obj.close()
                        raise ValueError(f"Failed to parse JSON: {stripped_line}") from e

            mmap_obj.close()
            if current_block:
                yield VitalBlock(current_block, triples_only=self.triples_only)  # Yield the last block if any
