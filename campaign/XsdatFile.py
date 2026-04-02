import struct

def read_bool(fp) -> bool:
    return struct.unpack("<?xxx", fp.read(4))[0]

def read_vector(fp) -> tuple[float, float, float]:
    return list(struct.unpack("<fff", fp.read(12)))

def read_int(fp) -> int:
    return struct.unpack("<i", fp.read(4))[0]

def read_float(fp) -> float:
    return struct.unpack("<f", fp.read(4))[0]

def read_string(fp) -> str:
    len = struct.unpack("<i", fp.read(4))[0]
    struct.unpack(f"{str(len)}s", fp.read(len))[0]
    
def skip_int(fp, len):
    struct.unpack(f"{len*4}s", fp.read(len * 4))

def write_bool(fp, flag: bool) -> None:
    fp.write(struct.pack("<?xxx", flag))
    
def write_vector(fp, vector: tuple[float, float, float]) -> None:
    fp.write(struct.pack("<fff", vector))

def write_int(fp, i: int) -> None:
    fp.write(struct.pack("<i", i))

def write_float(fp, f: float) -> None:
    fp.write(struct.pack("<f", f))

def write_string(fp, s: str) -> None:
    fp.write(struct.pack("<i", len(s)))
    s = bytes(s, 'utf-8')
    fp.write(struct.pack(f"{len(s)}s", s))