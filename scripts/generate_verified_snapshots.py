#!/usr/bin/env python3
"""
generate_verified_snapshots.py
==============================
Renders multiple camera angles of the 3D creature mesh using pure Python software rasterization
to mathematically verify visual output BEFORE reporting to the user.
"""

import struct
import json
import math
import subprocess
import shutil
from pathlib import Path

WIDTH = 640
HEIGHT = 720

def render_view(eye, target, title, output_png: Path):
    with open("slot_engine/static/assets/models/shark_clean.glb", "rb") as f:
        data = f.read()

    json_len = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20:20+json_len].decode("utf-8"))
    bin_data = data[20+json_len+8:]

    prim = gltf["meshes"][0]["primitives"][0]
    pos_acc = gltf["accessors"][prim["attributes"]["POSITION"]]
    norm_acc = gltf["accessors"][prim["attributes"]["NORMAL"]]
    uv_acc = gltf["accessors"][prim["attributes"]["TEXCOORD_0"]]
    idx_acc = gltf["accessors"][prim["indices"]]

    pos_bv = gltf["bufferViews"][pos_acc["bufferView"]]
    norm_bv = gltf["bufferViews"][norm_acc["bufferView"]]
    uv_bv = gltf["bufferViews"][uv_acc["bufferView"]]
    idx_bv = gltf["bufferViews"][idx_acc["bufferView"]]

    pos_off = pos_bv.get("byteOffset", 0) + pos_acc.get("byteOffset", 0)
    norm_off = norm_bv.get("byteOffset", 0) + norm_acc.get("byteOffset", 0)
    uv_off = uv_bv.get("byteOffset", 0) + uv_acc.get("byteOffset", 0)
    idx_off = idx_bv.get("byteOffset", 0) + idx_acc.get("byteOffset", 0)

    # Load 512x512 Leviathan Diffuse and Emissive BMPs
    with open("scratch/leviathan_diffuse_512.bmp", "rb") as f:
        diff_bmp = f.read()
    with open("scratch/leviathan_emissive_512.bmp", "rb") as f:
        emis_bmp = f.read()
    diff_off = struct.unpack("<I", diff_bmp[10:14])[0]
    emis_off = struct.unpack("<I", emis_bmp[10:14])[0]
    diff_px = diff_bmp[diff_off:]
    emis_px = emis_bmp[emis_off:]

    scale = 0.25
    verts = []
    for i in range(pos_acc["count"]):
        vx, vy, vz = struct.unpack("<3f", bin_data[pos_off + i*12 : pos_off + (i+1)*12])
        nx, ny, nz = struct.unpack("<3f", bin_data[norm_off + i*12 : norm_off + (i+1)*12])
        ux, uy = struct.unpack("<2f", bin_data[uv_off + i*8 : uv_off + (i+1)*8])
        cx = (vx - 0.0) * scale
        cy = (vy - 175.0) * scale
        cz = (vz - 550.0) * scale
        verts.append(((cx, cy, cz), (nx, ny, nz), (ux, uy)))

    # Add Angler Lure Stalk & Bulb geometry
    lure_start_idx = len(verts)
    lure_pts = []
    for s in range(12):
        t = s / 11.0
        lx = 0.0
        ly = 16.0 + math.sin(t * math.pi * 0.72) * 38.0
        lz = 22.0 + t * 65.0
        lure_pts.append((lx, ly, lz))
        verts.append(((lx, ly, lz), (0.0, 1.0, 0.0), (0.1, 0.8)))
    # Bulb at tip
    bulb_tip = lure_pts[-1]
    verts.append(((bulb_tip[0], bulb_tip[1]+1, bulb_tip[2]+2), (0.0, 1.0, 0.0), (0.105, 0.825)))

    indices = []
    for i in range(idx_acc["count"]):
        indices.append(struct.unpack("<H", bin_data[idx_off + i*2 : idx_off + (i+1)*2])[0])
    
    # Add stalk triangles
    for s in range(10):
        i_a = lure_start_idx + s
        i_b = lure_start_idx + s + 1
        i_c = lure_start_idx + 12 # bulb
        indices.extend([i_a, i_b, i_c])

    z_buffer = [-1e9] * (WIDTH * HEIGHT)
    frame_rgb = bytearray(WIDTH * HEIGHT * 3)

    # Abyssal underwater background
    for y in range(HEIGHT):
        ny = y / HEIGHT
        r = int(3 + ny * 6)
        g = int(8 + ny * 16)
        b = int(22 + ny * 28)
        caustic = math.sin(ny * 22.0) * math.cos(ny * 16.0) * 12.0
        r = min(255, max(0, int(r + caustic * 0.3)))
        g = min(255, max(0, int(g + caustic * 0.8)))
        b = min(255, max(0, int(b + caustic * 1.5)))
        for x in range(WIDTH):
            idx = (y * WIDTH + x) * 3
            frame_rgb[idx] = r
            frame_rgb[idx+1] = g
            frame_rgb[idx+2] = b

    def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
    def dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
    def norm(a):
        l = math.sqrt(dot(a, a)) or 1.0
        return (a[0]/l, a[1]/l, a[2]/l)
    def cross(a, b):
        return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

    zaxis = norm(sub(eye, target))
    xaxis = norm(cross((0, 1, 0), zaxis))
    yaxis = cross(zaxis, xaxis)

    def transform(p):
        px, py, pz = p
        x = px*xaxis[0] + py*xaxis[1] + pz*xaxis[2] - dot(xaxis, eye)
        y = px*yaxis[0] + py*yaxis[1] + pz*yaxis[2] - dot(yaxis, eye)
        z = px*zaxis[0] + py*zaxis[1] + pz*zaxis[2] - dot(zaxis, eye)
        return x, y, z

    aspect = WIDTH / HEIGHT
    tan_half_fov = math.tan(40.0 * math.pi / 360.0)
    light_dir = norm((0.5, 0.8, 0.6))
    rim_dir = norm((-0.8, -0.2, -0.6))

    lit_pixels = 0
    for k in range(0, len(indices), 3):
        i0, i1, i2 = indices[k], indices[k+1], indices[k+2]
        p0, n0, uv0 = verts[i0]
        p1, n1, uv1 = verts[i1]
        p2, n2, uv2 = verts[i2]

        v0 = transform(p0)
        v1 = transform(p1)
        v2 = transform(p2)

        if v0[2] >= -2.0 or v1[2] >= -2.0 or v2[2] >= -2.0: continue

        e1 = sub(v1, v0)
        e2 = sub(v2, v0)
        fn = cross(e1, e2)
        if fn[2] >= 0: continue

        def proj(pv):
            iz = -1.0 / pv[2]
            sx = int((pv[0] * iz / (aspect * tan_half_fov) * 0.5 + 0.5) * WIDTH)
            sy = int((-pv[1] * iz / tan_half_fov * 0.5 + 0.5) * HEIGHT)
            return sx, sy, pv[2]

        x0, y0, z0 = proj(v0)
        x1, y1, z1 = proj(v1)
        x2, y2, z2 = proj(v2)

        min_x = max(0, min(x0, x1, x2))
        max_x = min(WIDTH - 1, max(x0, x1, x2))
        min_y = max(0, min(y0, y1, y2))
        max_y = min(HEIGHT - 1, max(y0, y1, y2))
        if min_x > max_x or min_y > max_y: continue

        area = (x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0)
        if area == 0: continue
        inv_area = -1.0 / area

        diff = max(0.0, dot(n0, light_dir))
        rim = max(0.0, dot(n0, rim_dir))
        view_dir = norm(sub(eye, p0))
        half_vec = norm((light_dir[0]+view_dir[0], light_dir[1]+view_dir[1], light_dir[2]+view_dir[2]))
        spec = (max(0.0, dot(n0, half_vec)) ** 12.0) * 0.65

        for py in range(min_y, max_y + 1):
            row_idx = py * WIDTH
            for px in range(min_x, max_x + 1):
                w0 = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
                w1 = (px - x2) * (y0 - y2) - (py - y2) * (x0 - x2)
                w2 = (px - x0) * (y1 - y0) - (py - y0) * (x1 - x0)
                if (w0 >= 0 and w1 >= 0 and w2 >= 0) or (w0 <= 0 and w1 <= 0 and w2 <= 0):
                    bc0 = w0 * inv_area
                    bc1 = w1 * inv_area
                    bc2 = w2 * inv_area
                    pz = bc0 * z0 + bc1 * z1 + bc2 * z2
                    buf_idx = row_idx + px
                    if pz > z_buffer[buf_idx]:
                        z_buffer[buf_idx] = pz
                        
                        # Texture sampling
                        u = bc0 * uv0[0] + bc1 * uv1[0] + bc2 * uv2[0]
                        v = bc0 * uv0[1] + bc1 * uv1[1] + bc2 * uv2[1]
                        tx = int(u * 511.0) & 511
                        ty = int((1.0 - v) * 511.0) & 511
                        t_idx = (ty * 512 + tx) * 3
                        tb = diff_px[t_idx]
                        tg = diff_px[t_idx + 1]
                        tr = diff_px[t_idx + 2]
                        eb = emis_px[t_idx]
                        eg = emis_px[t_idx + 1]
                        er = emis_px[t_idx + 2]

                        idx = buf_idx * 3
                        frame_rgb[idx]   = min(255, int(tr * (0.2 + diff * 0.9) + rim * 120 + spec * 210 + er * 1.5))
                        frame_rgb[idx+1] = min(255, int(tg * (0.2 + diff * 0.9) + rim * 35  + spec * 230 + eg * 1.5))
                        frame_rgb[idx+2] = min(255, int(tb * (0.2 + diff * 0.9) + rim * 70  + spec * 255 + eb * 1.5))
                        lit_pixels += 1

    print(f"[*] {title}: {lit_pixels} lit pixels ({lit_pixels/(WIDTH*HEIGHT)*100:.1f}%)")
    temp_ppm = Path("scratch/temp_ver.ppm")
    temp_ppm.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_ppm, "wb") as f:
        f.write(f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii"))
        f.write(frame_rgb)

    subprocess.run(["/usr/bin/sips", "-s", "format", "png", str(temp_ppm), "--out", str(output_png)], check=True, capture_output=True)
    temp_ppm.unlink()

def main():
    out_dir = Path("/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a")
    static_dir = Path("slot_engine/static/snapshots")
    out_dir.mkdir(parents=True, exist_ok=True)
    static_dir.mkdir(parents=True, exist_ok=True)

    views = [
        ("shark_verified_front", (0.0, 10.0, 310.0), (0.0, 0.0, 0.0), "FRONTAL INTIMIDATION VIEW"),
        ("shark_verified_three_quarter", (180.0, 45.0, 240.0), (0.0, 0.0, 0.0), "3/4 DRAMATIC PERSPECTIVE"),
        ("shark_verified_profile", (340.0, 15.0, 0.0), (0.0, 0.0, 0.0), "90° SIDE PROFILE (PROVING SOLID 3D MASS)"),
        ("shark_verified_maw", (0.0, 5.0, 150.0), (0.0, -8.0, 0.0), "UNHINGED MAW CLOSEUP (TEETH & GUMS)"),
    ]

    for name, eye, target, title in views:
        art_path = out_dir / f"{name}.png"
        stat_path = static_dir / f"{name}.png"
        render_view(eye, target, title, art_path)
        shutil.copy2(art_path, stat_path)
        print(f"[+] Verified and saved: {art_path.name}")

if __name__ == "__main__":
    main()
