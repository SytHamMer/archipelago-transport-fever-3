"""Convert the Archipelago logo (PNG) into the notification icon of the mod (32 bit TGA), without extra dependencies.

Usage: python scripts/make_icon.py [source.png] [target.tga] [size]
The game loads "name.tga" from the file "name@2x.tga", so the target is named ap_icon@2x.tga.
"""
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "assets" / "archipelago_icon.png"
DEFAULT_TARGET = ROOT / "tf3_mod" / "archipelago_tf3_1" / "content" / "ap_icon@2x.tga"
DEFAULT_SIZE = 64

Pixel = tuple[int, int, int, int]


def _unfilter(rows: list[bytes], bytes_per_pixel: int) -> list[bytearray]:
    """Undo the PNG scanline filters (none, sub, up, average, Paeth)."""
    out: list[bytearray] = []
    previous = bytearray(len(rows[0]) - 1)
    for raw in rows:
        kind, line = raw[0], bytearray(raw[1:])
        for i in range(len(line)):
            left = line[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
            up = previous[i]
            up_left = previous[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
            if kind == 1:
                line[i] = (line[i] + left) & 255
            elif kind == 2:
                line[i] = (line[i] + up) & 255
            elif kind == 3:
                line[i] = (line[i] + (left + up) // 2) & 255
            elif kind == 4:
                estimate = left + up - up_left
                distances = (abs(estimate - left), abs(estimate - up), abs(estimate - up_left))
                best = (left, up, up_left)[distances.index(min(distances))]
                line[i] = (line[i] + best) & 255
        out.append(line)
        previous = line
    return out


def read_png(path: Path) -> tuple[int, int, list[Pixel]]:
    """Decode an 8 bit, non interlaced RGB or RGBA PNG into RGBA pixels, left to right, top to bottom."""
    data = Path(path).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG file"
    position, header, compressed = 8, None, b""
    while position < len(data):
        length, kind = struct.unpack(">I4s", data[position:position + 8])
        payload = data[position + 8:position + 8 + length]
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            compressed += payload
        position += 12 + length
    width, height, depth, color_type, _, _, interlace = header
    assert depth == 8 and interlace == 0 and color_type in (2, 6), "only 8 bit RGB/RGBA PNG files are supported"
    channels = 4 if color_type == 6 else 3
    stride = width * channels + 1
    raw = zlib.decompress(compressed)
    rows = _unfilter([raw[i * stride:(i + 1) * stride] for i in range(height)], channels)
    pixels: list[Pixel] = []
    for row in rows:
        for x in range(width):
            r, g, b = row[x * channels:x * channels + 3]
            pixels.append((r, g, b, row[x * channels + 3] if channels == 4 else 255))
    return width, height, pixels


def downscale(pixels: list[Pixel], width: int, height: int, size: int) -> list[Pixel]:
    """Shrink a square image to size x size by averaging blocks, weighting colors by opacity."""
    step_x, step_y = width // size, height // size
    out: list[Pixel] = []
    for block_y in range(size):
        for block_x in range(size):
            total_a = total_r = total_g = total_b = 0
            for y in range(block_y * step_y, (block_y + 1) * step_y):
                for x in range(block_x * step_x, (block_x + 1) * step_x):
                    r, g, b, a = pixels[y * width + x]
                    total_a += a
                    total_r += r * a
                    total_g += g * a
                    total_b += b * a
            count = step_x * step_y
            if total_a == 0:
                out.append((0, 0, 0, 0))
            else:
                out.append((round(total_r / total_a), round(total_g / total_a), round(total_b / total_a),
                            round(total_a / count)))
    return out


def write_tga(path: Path, size: int, pixels: list[Pixel]) -> None:
    """Uncompressed 32 bit TGA, rows stored bottom to top like the game's own icons."""
    header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, size, size, 32, 8)
    body = bytearray()
    for row in range(size - 1, -1, -1):
        for r, g, b, a in pixels[row * size:(row + 1) * size]:
            body += bytes((b, g, r, a))
    Path(path).write_bytes(header + bytes(body))


def convert(source: Path = DEFAULT_SOURCE, target: Path = DEFAULT_TARGET, size: int = DEFAULT_SIZE) -> Path:
    width, height, pixels = read_png(source)
    assert width == height and width % size == 0, "the source must be square with a size that is a multiple of the target"
    write_tga(target, size, downscale(pixels, width, height, size))
    return Path(target)


if __name__ == "__main__":
    args = sys.argv[1:]
    print(convert(*(Path(a) if i < 2 else int(a) for i, a in enumerate(args))))
