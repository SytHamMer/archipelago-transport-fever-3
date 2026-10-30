import struct
import zlib
from pathlib import Path

import make_icon

ASSET = Path(__file__).resolve().parent.parent / "assets" / "archipelago_icon.png"


def png_bytes(width, height, rows, color_type=6, filters=None):
    """A minimal PNG: `rows` are raw scanlines (bytes), optionally with a filter type per row."""
    filters = filters or [0] * height
    raw = b"".join(bytes([filters[i]]) + rows[i] for i in range(height))

    def chunk(kind, payload):
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def test_decode_rgba_without_filters(tmp_path):
    rows = [bytes([255, 0, 0, 255, 0, 255, 0, 128]), bytes([0, 0, 255, 255, 10, 20, 30, 0])]
    path = tmp_path / "a.png"
    path.write_bytes(png_bytes(2, 2, rows))
    width, height, pixels = make_icon.read_png(path)
    assert (width, height) == (2, 2)
    assert pixels == [(255, 0, 0, 255), (0, 255, 0, 128), (0, 0, 255, 255), (10, 20, 30, 0)]


def test_decode_handles_sub_and_up_filters(tmp_path):
    # filter 1 (sub): each byte is stored as the difference with the byte 4 positions to its left
    sub = bytes([10, 20, 30, 40, 5, 5, 5, 5])
    # filter 2 (up): each byte is stored as the difference with the byte above
    up = bytes([1, 1, 1, 1, 2, 2, 2, 2])
    path = tmp_path / "f.png"
    path.write_bytes(png_bytes(2, 2, [sub, up], filters=[1, 2]))
    _, _, pixels = make_icon.read_png(path)
    assert pixels[0] == (10, 20, 30, 40) and pixels[1] == (15, 25, 35, 45)
    assert pixels[2] == (11, 21, 31, 41) and pixels[3] == (17, 27, 37, 47)


def test_decode_rgb_gets_an_opaque_alpha(tmp_path):
    path = tmp_path / "rgb.png"
    path.write_bytes(png_bytes(1, 1, [bytes([1, 2, 3])], color_type=2))
    assert make_icon.read_png(path)[2] == [(1, 2, 3, 255)]


def test_downscale_averages_blocks_and_keeps_transparent_pixels_out_of_the_color():
    opaque_red = (200, 0, 0, 255)
    clear = (0, 0, 0, 0)
    pixels = [opaque_red, opaque_red, clear, clear] * 2 + [clear] * 8  # 4 wide, 4 high
    result = make_icon.downscale(pixels, 4, 4, 2)
    assert len(result) == 4
    assert result[0] == (200, 0, 0, 255)  # a fully opaque block keeps its color
    assert result[1] == (0, 0, 0, 0)
    assert result[2][3] == 0 and result[3][3] == 0


def test_downscale_half_transparent_block_keeps_the_color_not_a_darker_one():
    pixels = [(200, 100, 50, 255), (200, 100, 50, 255), (0, 0, 0, 0), (0, 0, 0, 0)]
    (r, g, b, a), = make_icon.downscale(pixels, 2, 2, 1)
    assert a == 128 or a == 127
    assert (r, g, b) == (200, 100, 50)


def test_tga_has_the_games_header_and_the_right_size(tmp_path):
    out = tmp_path / "icon@2x.tga"
    make_icon.write_tga(out, 2, [(1, 2, 3, 4)] * 4)
    data = out.read_bytes()
    assert data[2] == 2  # uncompressed true color
    assert struct.unpack("<HH", data[12:16]) == (2, 2)
    assert data[16] == 32 and data[17] == 8  # 32 bits per pixel, 8 alpha bits, origin at the bottom left
    assert len(data) == 18 + 2 * 2 * 4
    assert data[18:22] == bytes([3, 2, 1, 4])  # stored as BGRA


def test_tga_rows_are_stored_bottom_to_top(tmp_path):
    out = tmp_path / "icon.tga"
    top, bottom = (255, 0, 0, 255), (0, 0, 255, 255)
    make_icon.write_tga(out, 2, [top, top, bottom, bottom])
    body = out.read_bytes()[18:]
    assert body[:4] == bytes([255, 0, 0, 255])  # first stored row is the bottom row (blue, as BGRA)


def test_the_real_logo_converts_to_a_64_pixel_tga(tmp_path):
    out = tmp_path / "ap_icon@2x.tga"
    make_icon.convert(ASSET, out, 64)
    data = out.read_bytes()
    assert struct.unpack("<HH", data[12:16]) == (64, 64)
    assert len(data) == 18 + 64 * 64 * 4
    alphas = data[18 + 3::4]
    assert 0 in alphas and 255 in alphas  # the logo sits on a transparent background
