#!/usr/bin/env python3
"""
generate_volumetric_layers.py
High-Fidelity Organic Mandible Masking & PBR Normal Map Generator.
Contours an organic anatomical boundary around the lower jaw (chin, lower tusks,
bio-slime drips) with soft alpha feathering.
The cranium retains the entire dragon, so there is NEVER an empty hole.
"""

import math
import struct
import zlib
import subprocess
from pathlib import Path

def write_png(filepath: Path, width: int, height: int, rgba_bytes: bytes):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        start = y * width * 4
        raw.extend(rgba_bytes[start : start + width * 4])
    idat = zlib.compress(bytes(raw), 8)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(header)
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', idat))
        f.write(chunk(b'IEND', b''))

def load_image_rgb(src_jpg: Path):
    temp_bmp = Path("scratch/temp_src.bmp")
    temp_bmp.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["/usr/bin/sips", "-s", "format", "bmp", str(src_jpg), "--out", str(temp_bmp)], check=True, capture_output=True)
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

def process_creature_layers():
    src_art = Path("slot_engine/static/assets/sym_high_leviathan.jpg")
    out_dir = Path("slot_engine/static/assets/textures")
    brain_dir = Path("/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a")
    
    print(f"[*] Loading concept artwork from {src_art}...")
    w, h, rgb = load_image_rgb(src_art)

    cranium_rgba = bytearray(w * h * 4)
    mandible_rgba = bytearray(w * h * 4)
    throat_rgba = bytearray(w * h * 4)
    depth_rgba = bytearray(w * h * 4)

    print("[*] Generating Organic Mandible & Cranium Layers...")

    for y in range(h):
        ny = y / h
        for x in range(w):
            nx = x / w
            r, g, b = rgb[y][x]
            lum = 0.299 * r + 0.587 * g + 0.114 * b

            # Outer border soft vignette
            edge_x = min(nx, 1.0 - nx)
            edge_y = min(ny, 1.0 - ny)
            min_e = min(edge_x, edge_y)
            bg_alpha = 1.0
            if min_e < 0.05:
                bg_alpha = min_e / 0.05

            # Mandible Organic Polygon:
            # Elliptical / curved falloff around the lower jaw bone and chin:
            # Center of mandible bone is around (380, 660)
            # Extents: x ~ [300, 500], y ~ [545, 780]
            mand_cx = 390.0
            mand_cy = 660.0
            mand_rx = 105.0
            mand_ry = 115.0

            # Distance normalized to rotated jaw ellipse
            dx_m = (x - mand_cx)
            dy_m = (y - mand_cy)
            # Slight diagonal tilt (-15 deg)
            cos_t = 0.965
            sin_t = -0.258
            rot_dx = dx_m * cos_t - dy_m * sin_t
            rot_dy = dx_m * sin_t + dy_m * cos_t

            dist_mand = math.sqrt((rot_dx / mand_rx)**2 + (rot_dy / mand_ry)**2)
            
            # Mandible alpha: 1.0 inside ellipse, soft feather at boundary
            if dist_mand < 0.85:
                m_alpha = 1.0
            elif dist_mand < 1.15:
                m_alpha = 0.5 * (1.0 + math.cos((dist_mand - 0.85) / 0.30 * math.pi))
            else:
                m_alpha = 0.0

            # Only include pixels below upper teeth line (y > 540)
            upper_teeth_y = 550 + (490 - x) * 0.12 if x < 490 else 550
            if y < upper_teeth_y:
                m_alpha = 0.0

            # Cranium retains the ENTIRE image!
            # The cranium is 100% complete and uncompromised!
            c_final_a = int(bg_alpha * 255)
            m_final_a = int(m_alpha * bg_alpha * 255)

            c_idx = (y * w + x) * 4
            # 1. Cranium (Full Master Art with soft vignette)
            cranium_rgba[c_idx]   = r
            cranium_rgba[c_idx+1] = g
            cranium_rgba[c_idx+2] = b
            cranium_rgba[c_idx+3] = c_final_a

            # 2. Mandible (Isolated articulated lower jaw)
            mandible_rgba[c_idx]   = r
            mandible_rgba[c_idx+1] = g
            mandible_rgba[c_idx+2] = b
            mandible_rgba[c_idx+3] = m_final_a

            # 3. Deep Throat Cavity (Behind mouth opening x=400..480, y=510..600)
            throat_dx = (x - 430) / 70.0
            throat_dy = (y - 540) / 60.0
            throat_dist = math.sqrt(throat_dx*throat_dx + throat_dy*throat_dy)
            if throat_dist < 1.0:
                t_falloff = math.cos(throat_dist * math.pi * 0.5)
                tr = min(255, int(4 + t_falloff * 20))
                tg = min(255, int(22 + t_falloff * 140))
                tb = min(255, int(48 + t_falloff * 200))
                ta = min(255, int(t_falloff * 255))
            else:
                tr, tg, tb, ta = 0, 0, 0, 0

            throat_rgba[c_idx]   = tr
            throat_rgba[c_idx+1] = tg
            throat_rgba[c_idx+2] = tb
            throat_rgba[c_idx+3] = ta

            # 4. Sculptural Depth Displacement Map (Z height)
            snout_dist = math.sqrt(((x - 390)/160)**2 + ((y - 410)/150)**2)
            snout_h = max(0.0, 1.0 - snout_dist) * 160.0

            brow_dist = math.sqrt(((x - 490)/130)**2 + ((y - 310)/100)**2)
            brow_h = max(0.0, 1.0 - brow_dist) * 120.0

            chin_dist = math.sqrt(((x - 370)/120)**2 + ((y - 660)/110)**2)
            chin_h = max(0.0, 1.0 - chin_dist) * 110.0

            micro = (lum / 255.0) * 45.0

            depth_val = int(min(255, max(0, 35 + snout_h + brow_h + chin_h + micro)))
            depth_rgba[c_idx]   = depth_val
            depth_rgba[c_idx+1] = depth_val
            depth_rgba[c_idx+2] = depth_val
            depth_rgba[c_idx+3] = 255

    # 5. PBR Tangent Normal Map
    print("[*] Generating 3D Tangent Normal Map...")
    normal_rgba = bytearray(w * h * 4)
    strength = 3.2

    for y in range(h):
        y0 = max(0, y - 1)
        y1 = min(h - 1, y + 1)
        for x in range(w):
            x0 = max(0, x - 1)
            x1 = min(w - 1, x + 1)

            def get_d(px, py):
                return depth_rgba[(py * w + px) * 4]

            tl = get_d(x0, y0); t = get_d(x, y0); tr = get_d(x1, y0)
            l  = get_d(x0, y );                    r  = get_d(x1, y )
            bl = get_d(x0, y1); b = get_d(x, y1); br = get_d(x1, y1)

            dx = (tr + 2.0 * r + br) - (tl + 2.0 * l + bl)
            dy = (bl + 2.0 * b + br) - (tl + 2.0 * t + tr)

            nx = -dx * strength / 255.0
            ny = -dy * strength / 255.0
            nz = 1.0
            len_n = math.sqrt(nx*nx + ny*ny + nz*nz)
            nx /= len_n; ny /= len_n; nz /= len_n

            idx = (y * w + x) * 4
            normal_rgba[idx]   = int((nx * 0.5 + 0.5) * 255)
            normal_rgba[idx+1] = int((ny * 0.5 + 0.5) * 255)
            normal_rgba[idx+2] = int((nz * 0.5 + 0.5) * 255)
            normal_rgba[idx+3] = 255

    files_to_save = [
        ("leviathan_cranium_clean.png", cranium_rgba),
        ("leviathan_mandible_clean.png", mandible_rgba),
        ("leviathan_throat_clean.png", throat_rgba),
        ("leviathan_depth_map.png", depth_rgba),
        ("leviathan_normal_clean.png", normal_rgba),
    ]

    for fname, data in files_to_save:
        p1 = out_dir / fname
        p2 = brain_dir / fname
        write_png(p1, w, h, bytes(data))
        write_png(p2, w, h, bytes(data))
        print(f"    [+] Saved: {fname} ({w}x{h} RGBA)")

    print("\n[SUCCESS] Layers generated successfully!")

if __name__ == "__main__":
    process_creature_layers()
