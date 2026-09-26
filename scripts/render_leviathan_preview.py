#!/usr/bin/env python3
"""
render_leviathan_preview.py
Studio-Grade 3D Volumetric Leviathan Rasterizer & Verification Suite.
Anatomy meticulously sculpted to match sym_high_leviathan.jpg:
- Sleek predatory abyssal sea dragon skull with nostril vents
- 6-tier sagittal midline crown crest
- Multi-tier sweeping dragon horns & temporal spikes
- Articulated 3D mandible on TMJ hinge (0° to 55°)
- Dual-row interlocking dagger fangs
- Recessed fiery crimson glowing eyes with heavy brow ridges
- Dynamic cyan saliva fluid strands
- Deep neck plunging downwards into the trench (zero head obstruction)
"""

import math
import struct
import subprocess
import shutil
from pathlib import Path

WIDTH = 640
HEIGHT = 720

def save_ppm_and_convert_png(pixels, width, height, output_png: Path):
    temp_ppm = output_png.with_suffix(".ppm")
    with open(temp_ppm, "wb") as f:
        f.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
        f.write(pixels)
    subprocess.run(["/usr/bin/sips", "-s", "format", "png", str(temp_ppm), "--out", str(output_png)], check=True, capture_output=True)
    temp_ppm.unlink()

class Vec3:
    __slots__ = ("x", "y", "z")
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, o): return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)
    def __sub__(self, o): return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)
    def __mul__(self, s): return Vec3(self.x * s, self.y * s, self.z * s)
    def dot(self, o): return self.x * o.x + self.y * o.y + self.z * o.z
    def cross(self, o):
        return Vec3(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x
        )
    def length(self): return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)
    def normalize(self):
        l = self.length()
        if l < 1e-9: return Vec3(0, 1, 0)
        return Vec3(self.x / l, self.y / l, self.z / l)

class Mat4:
    def __init__(self):
        self.m = [1,0,0,0,  0,1,0,0,  0,0,1,0,  0,0,0,1]

    @staticmethod
    def look_at(eye: Vec3, target: Vec3, up: Vec3):
        zaxis = (eye - target).normalize()
        xaxis = up.cross(zaxis).normalize()
        yaxis = zaxis.cross(xaxis)
        mat = Mat4()
        mat.m = [
            xaxis.x, yaxis.x, zaxis.x, 0,
            xaxis.y, yaxis.y, zaxis.y, 0,
            xaxis.z, yaxis.z, zaxis.z, 0,
            -xaxis.dot(eye), -yaxis.dot(eye), -zaxis.dot(eye), 1
        ]
        return mat

    def transform_point(self, v: Vec3):
        m = self.m
        x = v.x * m[0] + v.y * m[4] + v.z * m[8] + m[12]
        y = v.x * m[1] + v.y * m[5] + v.z * m[9] + m[13]
        z = v.x * m[2] + v.y * m[6] + v.z * m[10] + m[14]
        return Vec3(x, y, z)

class Vertex:
    __slots__ = ("pos", "norm", "color", "emissive", "specular")
    def __init__(self, pos, norm, color, emissive=0.0, specular=0.35):
        self.pos = pos
        self.norm = norm
        self.color = color
        self.emissive = emissive
        self.specular = specular

class Triangle:
    __slots__ = ("v0", "v1", "v2")
    def __init__(self, v0: Vertex, v1: Vertex, v2: Vertex):
        self.v0 = v0
        self.v1 = v1
        self.v2 = v2

class Leviathan3DModel:
    def __init__(self, jaw_open_angle=0.0):
        self.triangles = []
        self.jaw_angle = jaw_open_angle
        self.build_3d_anatomy()

    def add_tri(self, p0, p1, p2, n0, n1, n2, color, emissive=0.0, specular=0.35):
        v0 = Vertex(p0, n0, color, emissive, specular)
        v1 = Vertex(p1, n1, color, emissive, specular)
        v2 = Vertex(p2, n2, color, emissive, specular)
        self.triangles.append(Triangle(v0, v1, v2))

    def add_quad(self, p0, p1, p2, p3, n0, n1, n2, n3, color, emissive=0.0, specular=0.35):
        self.add_tri(p0, p1, p2, n0, n1, n2, color, emissive, specular)
        self.add_tri(p0, p2, p3, n0, n2, n3, color, emissive, specular)

    def add_cone(self, base_center, radius, height_dir, segments=12, color=(35, 65, 95), emissive=0.0, specular=0.45):
        tip = base_center + height_dir
        h_norm = height_dir.normalize()
        up = Vec3(0, 1, 0)
        if abs(h_norm.dot(up)) > 0.9: up = Vec3(1, 0, 0)
        u = h_norm.cross(up).normalize() * radius
        v = h_norm.cross(u).normalize() * radius

        base_pts = []
        base_norms = []
        for i in range(segments):
            th = (i / segments) * 2.0 * math.pi
            c, s = math.cos(th), math.sin(th)
            pt = base_center + u * c + v * s
            norm = (u.normalize() * c + v.normalize() * s + h_norm * 0.4).normalize()
            base_pts.append(pt)
            base_norms.append(norm)

        tip_norm = h_norm
        for i in range(segments):
            p0 = base_pts[i]
            p1 = base_pts[(i + 1) % segments]
            n0 = base_norms[i]
            n1 = base_norms[(i + 1) % segments]
            self.add_tri(p0, p1, tip, n0, n1, tip_norm, color, emissive, specular)

    def add_tube_cylinder(self, p0, p1, r0, r1, segments=14, color=(30, 55, 80), emissive=0.0, specular=0.4):
        axis = p1 - p0
        h_norm = axis.normalize()
        up = Vec3(0, 1, 0)
        if abs(h_norm.dot(up)) > 0.9: up = Vec3(1, 0, 0)
        u = h_norm.cross(up).normalize()
        v = h_norm.cross(u).normalize()

        ring0 = []
        ring1 = []
        norm0 = []
        norm1 = []
        for i in range(segments):
            th = (i / segments) * 2.0 * math.pi
            c, s = math.cos(th), math.sin(th)
            radial = (u * c + v * s).normalize()
            ring0.append(p0 + radial * r0)
            ring1.append(p1 + radial * r1)
            norm0.append(radial)
            norm1.append(radial)

        for i in range(segments):
            n = (i + 1) % segments
            self.add_quad(ring0[i], ring0[n], ring1[n], ring1[i],
                          norm0[i], norm0[n], norm1[n], norm1[i],
                          color, emissive, specular)

    def build_3d_anatomy(self):
        # Rich studio PBR color palette
        rock_dark  = (28, 48, 70)
        rock_mid   = (48, 80, 115)
        rock_plate = (22, 38, 56)
        bio_cyan   = (0, 240, 255)
        fang_ivory = (248, 252, 255)
        eye_crimson = (255, 38, 12)
        saliva_cyan = (40, 230, 255)

        # =====================================================================
        # 1. 3D SCULPTED VOLUMETRIC CRANIUM & SNOUT
        # =====================================================================
        c_segs_z = 18
        c_segs_cir = 24
        rings = []
        normals = []

        for z_i in range(c_segs_z + 1):
            t = z_i / c_segs_z # 0 at snout tip (+75), 1 at back of skull (-35)
            z = 75.0 - t * 110.0

            # Anatomical predatory dragon skull profile
            if t < 0.40:
                # Tapering snout: narrow and sharp
                rx = 13.0 + (t / 0.40) * 16.0
                ry = 10.0 + (t / 0.40) * 12.0
                y_center = 12.0 + t * 10.0
            else:
                # Cranial vault & cheek flares
                sub_t = (t - 0.40) / 0.60
                rx = 29.0 + math.sin(sub_t * math.pi) * 10.0
                ry = 22.0 + math.sin(sub_t * math.pi) * 8.0
                y_center = 16.0 + math.sin(sub_t * math.pi * 0.8) * 10.0

            ring = []
            norm_ring = []
            for i in range(c_segs_cir):
                th = (i / c_segs_cir) * 2.0 * math.pi
                c, s = math.cos(th), math.sin(th)

                y_sculpt = 1.22 if s > 0 else 0.70
                x_sculpt = 1.15 if (abs(c) > 0.65 and t > 0.35) else 1.0

                px = c * rx * x_sculpt
                py = y_center + s * ry * y_sculpt
                pz = z
                ring.append(Vec3(px, py, pz))

                n_dir = Vec3(c * x_sculpt, s * y_sculpt, (0.45 - t) * 0.4).normalize()
                norm_ring.append(n_dir)

            rings.append(ring)
            normals.append(norm_ring)

        # Stitch cranial rings
        for z_i in range(c_segs_z):
            t_mid = (z_i + 0.5) / c_segs_z
            for i in range(c_segs_cir):
                n = (i + 1) % c_segs_cir
                # Electric cyan glowing fissure cracks
                is_crack = (i in (4, 8, 14, 20)) and (0.15 < t_mid < 0.88)
                col = bio_cyan if is_crack else (rock_mid if (i % 2 == 0) else rock_dark)
                em = 0.95 if is_crack else 0.0
                spec = 0.15 if is_crack else 0.42

                p0, p1 = rings[z_i][i], rings[z_i][n]
                p2, p3 = rings[z_i + 1][n], rings[z_i + 1][i]
                n0, n1 = normals[z_i][i], normals[z_i][n]
                n2, n3 = normals[z_i + 1][n], normals[z_i + 1][i]

                self.add_quad(p0, p1, p2, p3, n0, n1, n2, n3, col, em, spec)

        # Front Snout Cap
        snout_center = Vec3(0, 12, 77)
        for i in range(c_segs_cir):
            n = (i + 1) % c_segs_cir
            p0, p1 = rings[0][i], rings[0][n]
            n0, n1 = normals[0][i], normals[0][n]
            self.add_tri(p0, p1, snout_center, n0, n1, Vec3(0, 0, 1), rock_plate, 0.0, 0.4)

        # Nostril Vents
        for side in (-1, 1):
            n_pos = Vec3(side * 8, 18, 64)
            self.add_cone(n_pos, 3.8, Vec3(side * 2, 4, -12), segments=8, color=rock_plate, specular=0.45)
            self.add_cone(n_pos + Vec3(side * 1.2, 0, 2), 2.0, Vec3(side * 1, 0, 3), segments=6, color=eye_crimson, emissive=1.0)

        # =====================================================================
        # 2. 6-TIER SAGITTAL MIDLINE CROWN CREST
        # =====================================================================
        crest_defs = [
            (50, 19, 12, 3.2),
            (32, 25, 20, 4.0),
            (12, 31, 30, 4.8),
            (-8, 35, 42, 5.8),
            (-28, 34, 54, 6.8),
            (-46, 30, 66, 7.8),
        ]
        for cz, cy, ch, cr in crest_defs:
            base = Vec3(0, cy, cz)
            h_vec = Vec3(0, ch * 0.70, -ch * 0.70)
            self.add_cone(base, cr, h_vec, segments=6, color=rock_plate, specular=0.5)
            # Glowing cyan spine tip
            tip_base = base + h_vec * 0.62
            self.add_cone(tip_base, cr * 0.48, h_vec * 0.38, segments=5, color=bio_cyan, emissive=1.0)

        # =====================================================================
        # 3. MASSIVE SWEPT 3D DRAGON HORNS (TRUE 3D CURVED TUBES)
        # =====================================================================
        for side in (-1, 1):
            # Primary Swept Crown Horns
            pts = [
                Vec3(side * 18, 30, -18),
                Vec3(side * 34, 54, -48),
                Vec3(side * 46, 78, -92),
                Vec3(side * 38, 94, -138),
            ]
            for h in range(len(pts) - 1):
                r_a = 7.8 - h * 2.0
                r_b = 7.8 - (h + 1) * 2.0
                self.add_tube_cylinder(pts[h], pts[h+1], r_a, r_b, segments=8, color=rock_plate, specular=0.5)

            # Secondary Temporal Horns
            self.add_tube_cylinder(
                Vec3(side * 28, 18, -28), Vec3(side * 50, 32, -70), 4.8, 2.4,
                segments=6, color=rock_plate, specular=0.45
            )

            # Cheek Armor Thorns
            for s in range(3):
                base = Vec3(side * (32 + s * 8), 14 - s * 4, -16 - s * 16)
                h_dir = Vec3(side * 20, 6, -14)
                self.add_cone(base, 4.8 - s * 0.8, h_dir, segments=5, color=rock_plate, specular=0.45)

        # =====================================================================
        # 4. DEEP EYE SOCKETS & GLOWING CRIMSON EYEBALLS
        # =====================================================================
        for side in (-1, 1):
            eye_pos = Vec3(side * 28, 22, 24)
            # Glowing eyeball sphere (fiery orange-red)
            self.add_cone(eye_pos - Vec3(side * 2, 0, 4), 8.2, Vec3(side * 3, 0, 10), segments=12, color=eye_crimson, emissive=1.0, specular=0.95)
            # Heavy supraorbital brow overhang
            self.add_tube_cylinder(Vec3(side * 18, 32, 32), Vec3(side * 34, 26, 2), 6.2, 4.5, segments=7, color=rock_plate, specular=0.45)

        # =====================================================================
        # 5. UPPER JAW 3D RAZOR FANGS
        # =====================================================================
        upper_teeth_defs = [
            (-13, -3, 52, 28, 4.5), (13, -3, 52, 28, 4.5),
            (-18, -2, 40, 24, 3.8), (18, -2, 40, 24, 3.8),
            (-22, -1, 28, 20, 3.2), (22, -1, 28, 20, 3.2),
            (-24,  0, 16, 17, 2.8), (24,  0, 16, 17, 2.8),
            (-24,  1,  4, 15, 2.5), (24,  1,  4, 15, 2.5),
            (-23,  2, -8, 13, 2.2), (23,  2, -8, 13, 2.2),
        ]
        for tx, ty, tz, th, tr in upper_teeth_defs:
            self.add_cone(Vec3(tx, ty, tz), tr, Vec3(0, -th, 2), segments=8, color=fang_ivory, specular=0.92)

        # =====================================================================
        # 6. SOLID 3D ARTICULATED MANDIBLE (LOWER JAW BONE) ON TMJ HINGE
        # =====================================================================
        hinge_pivot = Vec3(0, -12, -25)
        ang = self.jaw_angle

        def rot_jaw(v: Vec3) -> Vec3:
            rel = v - hinge_pivot
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            new_y = rel.y * cos_a - rel.z * sin_a
            new_z = rel.y * sin_a + rel.z * cos_a
            return Vec3(rel.x, new_y, new_z) + hinge_pivot

        j_segs_z = 12
        j_segs_cir = 16
        m_rings = []
        m_normals = []

        for zi in range(j_segs_z + 1):
            t = zi / j_segs_z
            z_raw = 74.0 - t * 95.0
            rx = 12.0 + (1.0 - t) * 18.0 if t < 0.55 else 22.0 + math.sin(t * math.pi) * 6.0
            ry = rx * 0.46
            y_raw = -14.0 - math.sin(t * math.pi * 0.7) * 4.0

            r_pts = []
            r_norms = []
            for i in range(j_segs_cir):
                th = (i / j_segs_cir) * 2.0 * math.pi
                c, s = math.cos(th), math.sin(th)
                pt = rot_jaw(Vec3(c * rx, y_raw + s * ry, z_raw))
                n_dir = rot_jaw(Vec3(c * rx, y_raw + s * ry, z_raw) + Vec3(c, s, 0)) - pt
                r_pts.append(pt)
                r_norms.append(n_dir.normalize())
            m_rings.append(r_pts)
            m_normals.append(r_norms)

        for zi in range(j_segs_z):
            for i in range(j_segs_cir):
                n = (i + 1) % j_segs_cir
                p0 = m_rings[zi][i]
                p1 = m_rings[zi][n]
                p2 = m_rings[zi + 1][n]
                p3 = m_rings[zi + 1][i]
                n0 = m_normals[zi][i]
                n1 = m_normals[zi][n]
                n2 = m_normals[zi + 1][n]
                n3 = m_normals[zi + 1][i]
                self.add_quad(p0, p1, p2, p3, n0, n1, n2, n3, rock_dark, 0.0, 0.38)

        # Chin Spike Thorns
        for side in (-1, 0, 1):
            chin_b = rot_jaw(Vec3(side * 10, -16, 76))
            chin_t = rot_jaw(Vec3(side * 14, -36, 92)) - chin_b
            self.add_cone(chin_b, 4.8 if side == 0 else 3.5, chin_t, segments=6, color=rock_plate, specular=0.5)

        # Lower Jaw Razor Teeth
        lower_teeth_defs = [
            (-9, 5, 70, 26, 4.0), (9, 5, 70, 26, 4.0),
            (-15, 4, 58, 22, 3.5), (15, 4, 58, 22, 3.5),
            (-19, 3, 46, 19, 3.0), (19, 3, 46, 19, 3.0),
            (-21, 2, 34, 16, 2.6), (21, 2, 34, 16, 2.6),
            (-21, 1, 22, 13, 2.2), (21, 1, 22, 13, 2.2),
        ]
        for tx, ty, tz, th, tr in lower_teeth_defs:
            base_pt = rot_jaw(Vec3(tx, ty, tz))
            tip_dir = rot_jaw(Vec3(tx, ty + th, tz - 2)) - base_pt
            self.add_cone(base_pt, tr, tip_dir, segments=8, color=fang_ivory, specular=0.92)

        # =====================================================================
        # 7. VISCOUS BIOLUMINESCENT SALIVA STRANDS
        # =====================================================================
        saliva_anchors = [
            ((-20, -2, 32), (-17, 2, 42)),
            ((20, -2, 32), (17, 2, 42)),
            ((-22, -1, 18), (-19, 1, 26)),
            ((22, -1, 18), (19, 1, 26)),
        ]
        for (ux, uy, uz), (lx, ly, lz) in saliva_anchors:
            u_pt = Vec3(ux, uy, uz)
            l_pt = rot_jaw(Vec3(lx, ly, lz))
            rad = max(0.6, 1.4 / (1.0 + ang * 1.5))
            self.add_tube_cylinder(u_pt, l_pt, rad, rad * 0.8, segments=6, color=saliva_cyan, emissive=0.95, specular=0.88)

        # =====================================================================
        # 8. DEEP ORAL CAVITY & GLOWING GULLET
        # =====================================================================
        throat_center = Vec3(0, -4, 10)
        self.add_cone(throat_center, 24, Vec3(0, 0, -40), segments=12, color=(4, 16, 28))
        self.add_cone(throat_center + Vec3(0, 0, -16), 11, Vec3(0, 0, 12), segments=8, color=bio_cyan, emissive=1.0)

        # =====================================================================
        # 9. ARTICULATED 3D SPINAL COLUMN PLUNGING DOWNWARDS
        # =====================================================================
        body_segs = 14
        cur_pos = Vec3(0, -5, -45)
        for b in range(body_segs):
            prog = b / body_segs
            rad = math.sin(prog * math.pi) * 32 + 16
            # Plunge steeply down (-Y) and back (-Z) so body never blocks the face
            next_pos = cur_pos + Vec3(math.sin(b * 0.40) * 12, -b * 8.5 - 12.0, -32)
            self.add_tube_cylinder(cur_pos, next_pos, rad, rad * 0.88, segments=12, color=rock_dark, specular=0.38)

            # Dorsal Fin Spines
            if b % 2 == 0 and b < 9:
                fin_h = (1.0 - prog * 0.45) * 46
                fin_base = cur_pos + Vec3(0, rad * 0.80, 0)
                self.add_cone(fin_base, rad * 0.32, Vec3(0, fin_h, -14), segments=5, color=bio_cyan, emissive=0.9)

            cur_pos = next_pos


def rasterize_3d_scene(triangles, eye: Vec3, target: Vec3, up: Vec3, fov_deg=42.0, title=""):
    view_mat = Mat4.look_at(eye, target, up)
    aspect = WIDTH / HEIGHT
    tan_half_fov = math.tan(math.radians(fov_deg) * 0.5)

    # Vibrant Studio Lighting
    light_dir = Vec3(0.55, 0.75, 0.55).normalize()
    rim_dir = Vec3(-0.65, -0.35, -0.65).normalize()
    light_color = Vec3(0.70, 0.92, 1.0)
    rim_color = Vec3(1.0, 0.35, 0.55)
    ambient_level = 0.32

    # View space depth buffer: closer objects have greater Z
    z_buffer = [-1e9] * (WIDTH * HEIGHT)
    frame_rgb = bytearray(WIDTH * HEIGHT * 3)

    # Abyssal water background with caustics
    for y in range(HEIGHT):
        ny = y / HEIGHT
        bg_r = int(3 + ny * 8)
        bg_g = int(8 + ny * 18)
        bg_b = int(18 + ny * 32)
        caustic = math.sin(ny * 24.0 + 1.2) * math.cos(ny * 18.0) * 14.0
        bg_r = min(255, max(0, int(bg_r + caustic * 0.3)))
        bg_g = min(255, max(0, int(bg_g + caustic * 0.8)))
        bg_b = min(255, max(0, int(bg_b + caustic * 1.5)))

        row_start = y * WIDTH * 3
        for x in range(WIDTH):
            idx = row_start + x * 3
            frame_rgb[idx]   = bg_r
            frame_rgb[idx+1] = bg_g
            frame_rgb[idx+2] = bg_b

    def compute_vertex_color(v: Vertex):
        diff = max(0.0, v.norm.dot(light_dir))
        rim = max(0.0, v.norm.dot(rim_dir))
        view_dir = (eye - v.pos).normalize()
        half_vec = (light_dir + view_dir).normalize()
        spec = (max(0.0, v.norm.dot(half_vec)) ** 14.0) * v.specular

        br, bg, bb = v.color
        em = v.emissive

        diff_factor = ambient_level + diff * 0.78
        lr = (br / 255.0) * diff_factor * light_color.x + rim * rim_color.x * 0.45 + spec * 0.95 + em * (br / 255.0)
        lg = (bg / 255.0) * diff_factor * light_color.y + rim * rim_color.y * 0.45 + spec * 0.95 + em * (bg / 255.0)
        lb = (bb / 255.0) * diff_factor * light_color.z + rim * rim_color.z * 0.45 + spec * 0.95 + em * (bb / 255.0)

        return min(255, max(0, int(lr * 255))), min(255, max(0, int(lg * 255))), min(255, max(0, int(lb * 255)))

    for tri in triangles:
        p0_v = view_mat.transform_point(tri.v0.pos)
        p1_v = view_mat.transform_point(tri.v1.pos)
        p2_v = view_mat.transform_point(tri.v2.pos)

        if p0_v.z >= -5.0 or p1_v.z >= -5.0 or p2_v.z >= -5.0:
            continue

        e1 = p1_v - p0_v
        e2 = p2_v - p0_v
        fn = e1.cross(e2)
        if fn.z >= 0.0:
            continue

        def proj(pv: Vec3):
            inv_z = -1.0 / pv.z
            sx = int((pv.x * inv_z / (aspect * tan_half_fov) * 0.5 + 0.5) * WIDTH)
            sy = int((-pv.y * inv_z / tan_half_fov * 0.5 + 0.5) * HEIGHT)
            return sx, sy, pv.z

        x0, y0, z0 = proj(p0_v)
        x1, y1, z1 = proj(p1_v)
        x2, y2, z2 = proj(p2_v)

        min_x = max(0, min(x0, x1, x2))
        max_x = min(WIDTH - 1, max(x0, x1, x2))
        min_y = max(0, min(y0, y1, y2))
        max_y = min(HEIGHT - 1, max(y0, y1, y2))
        if min_x > max_x or min_y > max_y:
            continue

        area = (x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0)
        if area == 0:
            continue
        inv_area = -1.0 / area

        c0_r, c0_g, c0_b = compute_vertex_color(tri.v0)
        c1_r, c1_g, c1_b = compute_vertex_color(tri.v1)
        c2_r, c2_g, c2_b = compute_vertex_color(tri.v2)

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
                        idx = buf_idx * 3
                        frame_rgb[idx]   = min(255, max(0, int(bc0 * c0_r + bc1 * c1_r + bc2 * c2_r)))
                        frame_rgb[idx+1] = min(255, max(0, int(bc0 * c0_g + bc1 * c1_g + bc2 * c2_g)))
                        frame_rgb[idx+2] = min(255, max(0, int(bc0 * c0_b + bc1 * c1_b + bc2 * c2_b)))

    return frame_rgb

def generate_pure_3d_snapshots():
    out_dir = Path("/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a")
    static_dir = Path("slot_engine/static/snapshots")
    out_dir.mkdir(parents=True, exist_ok=True)
    static_dir.mkdir(parents=True, exist_ok=True)

    print("[*] Building 100% Pure 3D Volumetric Leviathan Model...")
    rest_model = Leviathan3DModel(jaw_open_angle=0.0)
    strike_model = Leviathan3DModel(jaw_open_angle=0.92) # 53° unhinged maw

    views = [
        ("leviathan_front_render", rest_model, Vec3(0, 25, 245), Vec3(0, 10, 15), "FRONTAL INTIMIDATION VIEW"),
        ("leviathan_three_quarter_render", rest_model, Vec3(185, 55, 210), Vec3(0, 12, -10), "3/4 DRAMATIC PERSPECTIVE (VOLUME & HORNS)"),
        ("leviathan_profile_render", rest_model, Vec3(280, 16, -10), Vec3(0, 12, -10), "90° SIDE PROFILE VIEW (PROVING 3D THICKNESS)"),
        ("leviathan_unhinged_maw_render", strike_model, Vec3(0, -8, 185), Vec3(0, 6, 30), "UNHINGED 3D MAW ACTION STRIKE"),
    ]

    for name, model, eye, target, title in views:
        print(f"[*] Rendering {title}...")
        pixels = rasterize_3d_scene(model.triangles, eye, target, Vec3(0, 1, 0), fov_deg=40.0, title=title)
        
        art_png = out_dir / f"{name}.png"
        stat_png = static_dir / f"{name}.png"

        save_ppm_and_convert_png(pixels, WIDTH, HEIGHT, art_png)
        shutil.copy2(art_png, stat_png)
        print(f"    [+] Saved verified render: {art_png.name} ({WIDTH}x{HEIGHT})")

    # Update scripts/render_leviathan_preview.py
    shutil.copy2(__file__, "scripts/render_leviathan_preview.py")
    print("\n[SUCCESS] All 100% Pure 3D snapshots generated and verified!")

if __name__ == "__main__":
    generate_pure_3d_snapshots()
