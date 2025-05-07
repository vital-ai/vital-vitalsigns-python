import io
import logging
import re
from rdflib import Graph, URIRef, Literal, BNode
import gzip
from io import StringIO

class NTriplesReader:
    def __init__(self, file_path):
        """
        Initialize the NTriplesReader with the path to the N-Triples file.

        :param file_path: Path to the N-Triples file (can be plain or gzipped).
        """
        self.file_path = file_path
        self.graph = Graph()

    def _open_file(self):
        """
        Open the file, handling both plain text and gzipped files.

        :return: A file-like object.
        """
        if self.file_path.endswith('.gz'):
            return gzip.open(self.file_path, 'rt', encoding='utf-8')
        return open(self.file_path, 'r', encoding='utf-8')

    def _extract_subject(self, line):
        """
        Extract the subject from a single N-Triples line.

        :param line: A line from the N-Triples file.
        :return: The subject URI as a string.
        """
        # match = re.match(r'<([^>]+)>', line)

        #subject = None

        # if match:
        #    subject = match.group(1)
            # logging.info(f"subject: {subject}")

        # return subject if match else None

        if line.startswith('<'):
            end_pos = line.find('>')
            if end_pos != -1:
                return line[1:end_pos]
        return None

    def read(self, chunk_size=100_000):
        """
        Read the N-Triples file line by line and yield triples grouped by subject.

        :param chunk_size: Number of lines to read at a time.
        :yield:
        """
        current_subject = None

        buffer = io.StringIO()

        line_count = 0

        with self._open_file() as file:

            for line in file:

                line = line.strip()

                # logging.info(f"line: {line}")

                subject = self._extract_subject(line)

                # logging.info(f"subject: {subject}")

                if not line or line.startswith('#'):
                    continue

                if subject is None:
                    continue

                if current_subject is None:
                    current_subject = subject

                if subject != current_subject and line_count >= chunk_size:
                    buffer.seek(0)
                    self.graph.parse(buffer, format="nt")
                    yield set(self.graph.triples((None, None, None)))
                    self.graph.remove((None, None, None))
                    buffer = io.StringIO()
                    line_count = 0

                current_subject = subject

                # Add the line to the buffer
                buffer.write(line + "\n")
                line_count += 1

            # Process any remaining lines in the buffer
            if buffer.tell() > 0:
                buffer.seek(0)
                self.graph.parse(buffer, format="nt")
                yield set(self.graph.triples((None, None, None)))
