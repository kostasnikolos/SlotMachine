#!/usr/bin/env python3
"""
render_composite_preview.py
Multi-Angle 3D Volumetric Verification Suite.
Renders the full seamless cranium + organic unhinged mandible in 3D perspective
with PBR lighting, normal mapping, and deep-sea caustics.
"""

import math
import struct
import zlib
import subprocess
from pathlib import Path

WIDTH = 640
HEIGHT = 720

def read_png_rgba(filepath: Path):
    with open(filepath, "rb") as f:
        png_bytes = f.read()
    
    pos = 8
    idat_acc = bytearray()
    w, h = 0, 0
    while pos < len(png_bytes):
        length = struct.unpack(">I", png_bytes[pos:pos+4])[0]
        tag = png_bytes[pos+4:pos+8]
        if tag == b"IHDR":
            w, h = struct.unpack(">II", png_bytes[pos+8:pos+16])
        elif tag == b"IDAT":
            idat_acc.extend(png_bytes[pos+8:pos+8+length])
        pos += 12 + length
        
    decomp = zlib.decompress(bytes(idat_acc))
    rgba_grid = []
    line_bytes = w * 4 + 1
    for y in range(h):
        row_raw = decomp[y * line_bytes + 1 : (y + 1) * line_bytes]
        row = []
        for x in range(w):
            idx = x * 4
            row.append((row_raw[idx], row_raw[idx+1], row_raw[idx+2], row_raw[idx+3]))
        rgba_grid.append(row)
        
    return w, h, rgba_grid

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
    idat = zlib.compress(bytes(raw), 8)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(header)
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', idat))
        f.write(chunk(b'IEND', b''))

def render_scene(cranium_img, mandible_img, throat_img, normal_img,
                 yaw_deg=0.0, pitch_deg=0.0, jaw_unhinge_deg=0.0, zoom=1.12):
    w_src = len(cranium_img[0])
    h_src = len(cranium_img)
    
    out_buf = bytearray(WIDTH * HEIGHT * 4)
    z_buf = [float('inf')] * (WIDTH * HEIGHT)

    # 1. Background: Deep Abyssal Trench with caustics and fog
    for y in range(HEIGHT):
        ny = y / HEIGHT
        bg_r = int(2 + ny * 6)
        bg_g = int(6 + ny * 14)
        bg_b = int(14 + ny * 24)
        
        caustic = math.sin(ny * 22.0 + 1.2) * math.cos(ny * 16.0) * 14.0
        bg_r = min(255, max(0, int(bg_r + caustic * 0.3)))
        bg_g = min(255, max(0, int(bg_g + caustic * 0.8)))
        bg_b = min(255, max(0, int(bg_b + caustic * 1.5)))

        for x in range(WIDTH):
            idx = (y * WIDTH + x) * 4
            out_buf[idx]   = bg_r
            out_buf[idx+1] = bg_g
            out_buf[idx+2] = bg_b
            out_buf[idx+3] = 255

    rad_yaw = math.radians(yaw_deg)
    rad_pitch = math.radians(pitch_deg)
    rad_jaw = math.radians(jaw_unhinge_deg)

    hinge_x = 495.0
    hinge_y = 540.0

    layers = [
        ("THROAT", throat_img, 0.0, -15.0),
        ("CRANIUM", cranium_img, 0.0, 0.0),
        ("MANDIBLE", mandible_img, rad_jaw, 4.0),
    ]

    for layer_name, img, jaw_rot, base_z in layers:
        step = 2
        for sy in range(0, h_src, step):
            for sx in range(0, w_src, step):
                r, g, b, a = img[sy][sx]
                if a < 10:
                    continue

                # 3D Base Coordinates (Centered around 512, 512)
                lx = (sx - 512) * 0.38 * zoom
                ly = (512 - sy) * 0.38 * zoom # Y up
                lz = base_z

                # Convex 3D displacement
                dist_snout = math.sqrt(((sx - 390) / 160)**2 + ((sy - 410) / 150)**2)
                snout_z = max(0.0, 1.0 - dist_snout) * 36.0 * zoom
                dist_edge = math.sqrt(((sx - 512)/512)**2 + ((sy - 512)/512)**2)
                edge_z = -math.pow(dist_edge, 1.8) * 35.0 * zoom

                lz += (snout_z + edge_z)

                # Jaw unhinge rotation around hinge pivot
                if jaw_rot != 0.0:
                    rel_y = (512 - sy) - (512 - hinge_y)
                    rel_z = lz - base_z
                    rot_y = rel_y * math.cos(jaw_rot) - rel_z * math.sin(jaw_rot)
                    rot_z = rel_y * math.sin(jaw_rot) + rel_z * math.cos(jaw_rot)
                    ly = (rot_y + (512 - hinge_y)) * 0.38 * zoom
                    # Jaw lunges forward (+Z) as it drops
                    lz = base_z + rot_z + math.sin(jaw_rot) * 22.0 * zoom

                # 3D Camera Rotation (Yaw & Pitch)
                x_yaw = lx * math.cos(rad_yaw) + lz * math.sin(rad_yaw)
                z_yaw = -lx * math.sin(rad_yaw) + lz * math.cos(rad_yaw)

                y_pitch = ly * math.cos(rad_pitch) - z_yaw * math.sin(rad_pitch)
                z_cam = ly * math.sin(rad_pitch) + z_yaw * math.cos(rad_pitch)

                cam_dist = 420.0
                depth = cam_dist - z_cam
                if depth < 10.0: continue

                fov_scale = cam_dist / depth
                px = int(WIDTH * 0.5 + x_yaw * fov_scale)
                py = int(HEIGHT * 0.50 - y_pitch * fov_scale)

                if px < 0 or px >= WIDTH or py < 0 or py >= HEIGHT:
                    continue

                idx_z = py * WIDTH + px
                # Allow slight layer bias so mandible sits cleanly in front of cranium
                layer_bias = -2.0 if layer_name == "MANDIBLE" else 0.0
                if depth + layer_bias < z_buf[idx_z]:
                    z_buf[idx_z] = depth + layer_bias

                    # PBR Normal lighting
                    norm_r, norm_g, norm_b, _ = normal_img[sy][sx]
                    nx = (norm_r / 255.0) * 2.0 - 1.0
                    ny = (norm_g / 255.0) * 2.0 - 1.0
                    nz = (norm_b / 255.0) * 2.0 - 1.0

                    diff = max(0.0, nx * 0.35 + ny * 0.6 + nz * 0.7)
                    rim = max(0.0, -nx * 0.5 - ny * 0.3 + nz * 0.2)

                    lit_r = min(255, int(r * (0.85 + diff * 0.35) + rim * 35))
                    lit_g = min(255, int(g * (0.85 + diff * 0.45) + rim * 12))
                    lit_b = min(255, int(b * (0.85 + diff * 0.55) + rim * 20))

                    alpha_f = a / 255.0
                    buf_idx = idx_z * 4
                    bg_r = out_buf[buf_idx]
                    bg_g = out_buf[buf_idx+1]
                    bg_b = out_buf[buf_idx+2]

                    out_buf[buf_idx]   = int(lit_r * alpha_f + bg_r * (1.0 - alpha_f))
                    out_buf[buf_idx+1] = int(lit_g * alpha_f + bg_g * (1.0 - alpha_f))
                    out_buf[buf_idx+2] = int(lit_b * alpha_f + bg_b * (1.0 - alpha_f))
                    out_buf[buf_idx+3] = 255

    return out_buf

def main():
    tex_dir = Path("slot_engine/static/assets/textures")
    brain_dir = Path("/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a")
    snap_dir = Path("slot_engine/static/snapshots")

    print("[*] Loading generated anatomical layers...")
    _, _, cranium = read_png_rgba(tex_dir / "leviathan_cranium_clean.png")
    _, _, mandible = read_png_rgba(tex_dir / "leviathan_mandible_clean.png")
    _, _, throat = read_png_rgba(tex_dir / "leviathan_throat_clean.png")
    _, _, normal = read_png_rgba(tex_dir / "leviathan_normal_clean.png")

    views = [
        ("leviathan_front_render", 0.0, 0.0, 0.0, 1.15, "FRONTAL INTIMIDATION VIEW"),
        ("leviathan_three_quarter_render", 26.0, 8.0, 0.0, 1.15, "3/4 DRAMATIC PERSPECTIVE (DEPTH & HORNS)"),
        ("leviathan_unhinged_maw_render", 10.0, -4.0, 38.0, 1.25, "UNHINGED MAW ACTION STRIKE (OPEN GULLET & FANGS)"),
    ]

    for name, yaw, pitch, jaw_ang, zoom, title in views:
        print(f"[*] Rendering {title}...")
        pixels = render_scene(cranium, mandible, throat, normal,
                              yaw_deg=yaw, pitch_deg=pitch, jaw_unhinge_deg=jaw_ang, zoom=zoom)
        
        p_brain = brain_dir / f"{name}.png"
        p_snap = snap_dir / f"{name}.png"

        write_png_rgba(p_brain, WIDTH, HEIGHT, pixels)
        write_png_rgba(p_snap, WIDTH, HEIGHT, pixels)
        print(f"    [+] Saved verified render: {p_brain.name} ({WIDTH}x{HEIGHT})")

    print("\n[SUCCESS] Final verification renders completed and saved!")

if __name__ == "__main__":
    main()
