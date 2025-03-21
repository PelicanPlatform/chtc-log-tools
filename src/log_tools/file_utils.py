import os
import gzip
import magic
from pathlib import Path

def read_file_reverse(file_path: Path, chunk_size=40960):
    """Reads a regular or compressed (.gz) text file line by line in reverse order using chunk-based processing."""
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)
    is_compressed = 'gzip' in file_type
    
    open_func = gzip.open if is_compressed else open
    
    with open_func(file_path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

        buffer = None
        position = file_size

        while position > 0:
            read_size = min(chunk_size, position)
            position -= read_size

            f.seek(position)
            chunk = f.read(read_size)

            lines = chunk.split(b'\n')

            if buffer is not None:
                if chunk[-1] == b'\n':
                    yield buffer  # Yield previous buffer since it's complete
                else:
                    lines[-1] += buffer  # Merge buffer with last line of current chunk

            buffer = lines.pop(0) if position != 0 else None  # Save first line for next chunk

            # Yield non-empty lines in reverse order
            for line in reversed(lines):
                if line.strip():
                    yield line.decode()

        # Yield the last buffered line if it's valid
        if buffer and buffer.strip():
            yield buffer
