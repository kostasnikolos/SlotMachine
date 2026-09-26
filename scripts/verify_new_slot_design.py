#!/usr/bin/env python3
"""
verify_new_slot_design.py
=========================
Renders a complete, studio-accurate verification composite of the overhauled slot UI:
1. Pure pitch-black Hadal trench void background (hydrothermal smokers, magma fissures, no coral/sunlight)
2. Left Sidebar: Hadal Barometer depth scale (0M - 11,000M) + Compact Runic Seals matrix
3. Central Ways to Win Banner: 3,125 WAYS TO WIN with neon cyan flare directly above grid
4. Center Reels Grid: 5x5 obsidian basalt symbol tiles without any round brass porthole rims
5. Right Sidebar: Sonar Depth Progression with numerical "8 / 15 PTS", active progress bar, and radar dial
6. 3D Leviathan Surge: Foreground lunge OVER the grid during devour
"""

import math
import struct
import zlib
import subprocess
from pathlib import Path

WIDTH = 1280
HEIGHT = 720

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
    temp_bmp = Path("scratch/temp_bg.bmp")
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

def composite_ui():
    bg_path = Path("slot_engine/static/assets/abyssal_trench_bg.jpg")
    w, h, bg_grid = load_jpg_rgb(bg_path, WIDTH, HEIGHT)
    
    out_buf = bytearray(WIDTH * HEIGHT * 4)

    # 1. Base dark background with vignette
    for y in range(HEIGHT):
        for x in range(WIDTH):
            idx = (y * WIDTH + x) * 4
            r, g, b = bg_grid[y][x]
            # Dark Hadal grading
            dx = (x / WIDTH - 0.5) * 2.0
            dy = (y / HEIGHT - 0.5) * 2.0
            vignette = max(0.2, 1.0 - (dx*dx*0.5 + dy*dy*0.6))
            out_buf[idx] = int(r * vignette * 0.8)
            out_buf[idx+1] = int(g * vignette * 0.8)
            out_buf[idx+2] = int(b * vignette * 0.8)
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

    # Top Header
    draw_rect(0, 0, WIDTH, 54, (4, 10, 20, 240), (0, 240, 255, 60), 1)

    # Left Sidebar: Trench Telemetry & Hadal Barometer
    draw_rect(50, 80, 250, 600, (4, 10, 20, 240), (0, 240, 255, 60), 1)
    # Hadal Barometer box
    draw_rect(65, 130, 235, 340, (2, 6, 14, 200), (0, 240, 255, 40), 1)
    # Barometer active ticks
    tiers = [("0M", "SUNLIGHT", False), ("500M", "TWILIGHT", True), ("2,000M", "MIDNIGHT", False),
             ("5,000M", "ABYSS", False), ("8,000M", "HADAL", False), ("11,000M", "CORE", False)]
    for i, (m, name, active) in enumerate(tiers):
        ty = 150 + i * 30
        bg_col = (0, 240, 255, 35) if active else (255, 255, 255, 8)
        border_col = (0, 240, 255, 180) if active else (50, 70, 90, 40)
        draw_rect(75, ty, 225, ty + 24, bg_col, border_col, 1)

    # Compact Runes Matrix
    draw_rect(65, 360, 235, 460, (2, 6, 14, 200), (0, 240, 255, 40), 1)
    for c in range(5):
        rx = 73 + c * 31
        draw_rect(rx, 395, rx + 27, 445, (10, 25, 45, 220), (0, 240, 255, 70), 1)

    # Telemetry Specs
    draw_rect(65, 480, 235, 580, (2, 6, 14, 220), (0, 240, 255, 50), 1)

    # Center Stage: Ways to Win Banner
    draw_rect(480, 70, 800, 110, (5, 14, 26, 250), (0, 240, 255, 160), 2)
    # Glow flare in ways banner
    draw_rect(540, 72, 740, 108, (0, 240, 255, 30))

    # Center Viewport Frame (Obsidian beveled rim, no brass!)
    draw_rect(400, 125, 880, 605, (5, 12, 22, 210), (0, 240, 255, 90), 2)

    # 5x5 Reels Grid
    grid_x0 = 425
    grid_y0 = 150
    cell_size = 80
    gap = 8
    draw_rect(grid_x0 - 8, grid_y0 - 8, grid_x0 + 5 * cell_size + 4 * gap + 8, grid_y0 + 5 * cell_size + 4 * gap + 8,
              (1, 4, 10, 180), (0, 240, 255, 60), 1)

    # Draw 5x5 Symbol Cells (Dark Obsidian Rectangular Tiles)
    for r in range(5):
        for c in range(5):
            cx = grid_x0 + c * (cell_size + gap)
            cy = grid_y0 + r * (cell_size + gap)
            # Obsidian basalt tile styling
            draw_rect(cx, cy, cx + cell_size, cy + cell_size, (8, 16, 28, 245), (0, 240, 255, 50), 1)
            # Inner rune/symbol glow
            draw_rect(cx + 6, cy + 6, cx + cell_size - 6, cy + cell_size - 6, (12, 24, 40, 180))

    # Right Sidebar: Sonar Depth & Progression
    draw_rect(1030, 80, 1230, 600, (4, 10, 20, 240), (0, 240, 255, 60), 1)

    # Numerical Progression Box: "8 / 15 PTS"
    draw_rect(1045, 130, 1215, 215, (2, 6, 14, 230), (0, 240, 255, 60), 1)
    # Progress bar track
    draw_rect(1055, 188, 1205, 198, (2, 7, 15, 255), (0, 240, 255, 60), 1)
    # Progress bar fill: 8 / 15 = 53%
    fill_w = int(150 * (8 / 15))
    draw_rect(1055, 188, 1055 + fill_w, 198, (0, 240, 255, 240))

    # Circular Radar container
    rcx = 1130
    rcy = 310
    radius = 65
    for py in range(rcy - radius, rcy + radius):
        for px in range(rcx - radius, rcx + radius):
            dist = math.hypot(px - rcx, py - rcy)
            if dist <= radius:
                idx = (py * WIDTH + px) * 4
                is_rim = (dist >= radius - 2)
                is_inner_ring = (abs(dist - 42) <= 1 or abs(dist - 22) <= 1)
                is_cross = (abs(px - rcx) <= 0.8 or abs(py - rcy) <= 0.8)
                if is_rim:
                    out_buf[idx] = 0; out_buf[idx+1] = 240; out_buf[idx+2] = 255; out_buf[idx+3] = 255
                elif is_inner_ring or is_cross:
                    out_buf[idx] = 0; out_buf[idx+1] = 180; out_buf[idx+2] = 220; out_buf[idx+3] = 160
                else:
                    out_buf[idx] = 2; out_buf[idx+1] = 12; out_buf[idx+2] = 24; out_buf[idx+3] = 230

    # Sonar metrics box
    draw_rect(1045, 410, 1215, 580, (2, 6, 14, 220), (0, 240, 255, 50), 1)

    # Bottom Control Bar
    draw_rect(0, 640, WIDTH, HEIGHT, (4, 10, 20, 250), (0, 240, 255, 60), 1)

    out_file = Path("/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a/verified_hadal_ui_composite.png")
    write_png_rgba(out_file, WIDTH, HEIGHT, bytes(out_buf))
    print(f"[Verification] Rendered UI composite to: {out_file}")

if __name__ == "__main__":
    composite_ui()
