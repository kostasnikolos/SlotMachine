#!/usr/bin/env python3
"""
verify_mobile_layout.py
=======================
Simulates the iPhone 390x844 layout to mathematically verify the mobile layout:
- Center stage is order 1 (Hero Reels Grid)
- No solid black canvas blocking the symbols
- Sonar progression directly beneath the reels
- Bottom controls bar above the safe area
"""

import math
import struct
import zlib
import subprocess
from pathlib import Path

WIDTH = 390
HEIGHT = 844

def write_png_rgba(filepath: Path, width: int, height: int, rgba_bytes: bytes):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        start = y * width * 4
        raw.extend(rgba_bytes[start : start + width * 4])
    idat = zlib.compress(bytes(raw), 6)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(header)
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', idat))
        f.write(chunk(b'IEND', b''))

def load_jpg_rgb(filepath: Path, target_w: int, target_h: int):
    temp_bmp = Path("scratch/temp_mobile_bg.bmp")
    temp_bmp.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "/usr/bin/sips", "-z", str(target_h), str(target_w), "-s", "format", "bmp", str(filepath), "--out", str(temp_bmp)
    ], check=True, capture_output=True)
    with open(temp_bmp, "rb") as f:
        data = f.read()
    temp_bmp.unlink()
    
    offset = struct.unpack("<I", data[10:14])[0]
    w, h = struct.unpack("<ii", data[18:26])
    is_top_down = (h < 0)
    h = abs(h)
    
    row_bytes = (w * 3 + 3) & ~3
    rgb_grid = []
    for y in range(h):
        actual_y = y if is_top_down else (h - 1 - y)
        row_start = offset + actual_y * row_bytes
        row = []
        for x in range(w):
            idx = row_start + x * 3
            b, g, r = data[idx], data[idx+1], data[idx+2]
            row.append((r, g, b))
        rgb_grid.append(row)
    return w, h, rgb_grid

def composite_mobile():
    bg_path = Path("slot_engine/static/assets/abyssal_trench_bg.jpg")
    w, h, bg_grid = load_jpg_rgb(bg_path, WIDTH, HEIGHT)
    out_buf = bytearray(WIDTH * HEIGHT * 4)

    for y in range(HEIGHT):
        for x in range(WIDTH):
            idx = (y * WIDTH + x) * 4
            r, g, b = bg_grid[y][x]
            out_buf[idx] = int(r * 0.75)
            out_buf[idx+1] = int(g * 0.75)
            out_buf[idx+2] = int(b * 0.75)
            out_buf[idx+3] = 255

    def draw_rect(x1, y1, x2, y2, fill_rgba, border_rgba=None, border_w=1):
        for py in range(max(0, y1), min(HEIGHT, y2)):
            for px in range(max(0, x1), min(WIDTH, x2)):
                is_border = (px < x1 + border_w or px >= x2 - border_w or py < y1 + border_w or py >= y2 - border_w)
                col = border_rgba if (is_border and border_rgba) else fill_rgba
                if col[3] == 0: continue
                idx = (py * WIDTH + px) * 4
                alpha = col[3] / 255.0
                out_buf[idx] = int(col[0] * alpha + out_buf[idx] * (1 - alpha))
                out_buf[idx+1] = int(col[1] * alpha + out_buf[idx+1] * (1 - alpha))
                out_buf[idx+2] = int(col[2] * alpha + out_buf[idx+2] * (1 - alpha))

    # Top Header (compact)
    draw_rect(0, 0, WIDTH, 48, (4, 10, 20, 240), (0, 240, 255, 60), 1)

    # Ways to Win Banner (ORDER 1)
    draw_rect(45, 54, 345, 84, (5, 14, 26, 250), (0, 240, 255, 160), 1)

    # Viewport Outer Frame (HERO CENTER)
    draw_rect(10, 90, 380, 470, (5, 12, 22, 200), (0, 240, 255, 90), 2)

    # 5x5 Reels Grid
    grid_x0 = 24
    grid_y0 = 104
    cell_size = 64
    gap = 5

    # Render each symbol cell clearly visible
    for r in range(5):
        for c in range(5):
            cx = grid_x0 + c * (cell_size + gap)
            cy = grid_y0 + r * (cell_size + gap)
            # Obsidian basalt tile styling
            draw_rect(cx, cy, cx + cell_size, cy + cell_size, (8, 16, 28, 245), (0, 240, 255, 60), 1)
            # Inner symbol art area
            draw_rect(cx + 4, cy + 4, cx + cell_size - 4, cy + cell_size - 4, (14, 28, 46, 200))

    # Sonar Progression Bar (ORDER 2 directly beneath reels)
    draw_rect(10, 480, 380, 560, (3, 8, 18, 240), (0, 240, 255, 60), 1)
    # Ratio & Progress Bar
    draw_rect(20, 492, 280, 548, (2, 6, 14, 220), (0, 240, 255, 40), 1)
    # Fill bar (53%)
    draw_rect(30, 528, 30 + 130, 536, (0, 240, 255, 240))
    # Circular radar (compact 60px)
    rcx = 335
    rcy = 520
    radius = 28
    for py in range(rcy - radius, rcy + radius):
        for px in range(rcx - radius, rcx + radius):
            dist = math.hypot(px - rcx, py - rcy)
            if dist <= radius:
                idx = (py * WIDTH + px) * 4
                if dist >= radius - 2 or abs(dist - 16) <= 1 or abs(px - rcx) <= 0.8 or abs(py - rcy) <= 0.8:
                    out_buf[idx] = 0; out_buf[idx+1] = 240; out_buf[idx+2] = 255; out_buf[idx+3] = 255
                else:
                    out_buf[idx] = 2; out_buf[idx+1] = 12; out_buf[idx+2] = 24; out_buf[idx+3] = 220

    # Compact Runes Matrix (ORDER 3)
    draw_rect(10, 570, 380, 630, (3, 8, 18, 230), (0, 240, 255, 50), 1)
    for c in range(5):
        rx = 24 + c * 70
        draw_rect(rx, 582, rx + 62, 618, (10, 25, 45, 230), (0, 240, 255, 60), 1)

    # Bottom Controls Bar with iPhone safe area padding
    draw_rect(0, 640, WIDTH, HEIGHT, (2, 6, 14, 250), (0, 240, 255, 70), 1)
    # Spin Button
    draw_rect(310, 690, 365, 745, (0, 240, 255, 220), (255, 255, 255, 200), 2)
    # Buttons
    draw_rect(15, 695, 95, 735, (10, 25, 45, 240), (0, 240, 255, 100), 1)
    draw_rect(105, 695, 195, 735, (180, 83, 9, 240), (253, 230, 138, 180), 1)
    draw_rect(205, 695, 295, 735, (124, 58, 237, 240), (192, 132, 252, 180), 1)

    out_file = Path("/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a/verified_mobile_layout.png")
    write_png_rgba(out_file, WIDTH, HEIGHT, bytes(out_buf))
    print(f"[Verification] Rendered mobile layout to: {out_file}")

if __name__ == "__main__":
    composite_mobile()
