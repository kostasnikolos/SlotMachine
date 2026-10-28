#!/usr/bin/env python3
"""Turn the three raw Tripo GLBs (≈2M tris, 67 MB each) into light game GLBs.

For each part: parse GLB -> weld + quadric decimation that preserves UVs (pymeshlab)
-> rebuild per-vertex UVs/normals -> downsized textures + a cyan-vein emissive map
-> bake the hi-poly onto the low-poly UV atlas: an object-space normal map (all of the
   sculpted relief the decimation threw away), ray-traced ambient occlusion and a
   thinness (shape-diameter) map -> write the web assets. Re-run any time:
    pip install pymeshlab numpy pillow scipy && python3 scripts/descent/build_leviathan.py [head|body|tail ...]
Inputs: the raw Tripo GLBs in artifacts/. Outputs: slot_engine/static/assets/descent/lev_*.json + lev_*_{base,normal,mr,emissive}.jpg

Map layout (flagged in lev_*.json so older JSON keeps the old meaning):
  normal  'nrm': 'object'  -> RGB = hi-poly normal in creature space (x along the spine, y dorsal, z side), *0.5+0.5
  mr      'mr': 'ao-rough-thin' -> R = baked ambient occlusion, G = roughness (Tripo), B = thinness (1 = thin: spines, teeth, fins)
  head    'eyes': [{c, n, r}] -> eye centres / outward normals / radii in head creature space (from the painted red irises)
"""
import io
import json
import os
import struct
import sys

import tempfile

import numpy as np
import pymeshlab
from PIL import Image

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'artifacts')
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.environ.get('LEV_OUT', os.path.join(REPO, 'slot_engine', 'static', 'assets', 'descent'))
PARTS = [
    ('head', 'dragon head 3d model.glb', 40000),
    ('body', 'spiked cylinder 3d model.glb', 18000),
    ('tail', 'dragon tail 3d model_Clone1.glb', 16000),
]
TEX = 2048
BAKE = 2048       # baked normal / AO / thinness resolution
AO_RAYS = 128

# Creature space written into the GLBs: x = along the spine (0 = joint, + toward the tail),
# y = dorsal, z = side, all in units of the body radius, so the swim shader can bend them.
#   keep: (lo, hi) range of the source Z kept (crops uneven spines at section ends)
#   r: source half-width of the cross-section; front: source Z of the front cut; cy: source Y of the centre line
RIG = {
    'head': {'kind': 'rigid', 'anchor': (0.20, 0.24, 0.0), 'r': 0.207},
    'body': {'kind': 'chain', 'keep': (-0.36, 0.30), 'front': 0.30, 'cy': 0.15, 'r': 0.167},
    'tail': {'kind': 'chain', 'keep': (-1.0, 0.36), 'front': 0.36, 'cy': 0.235, 'r': 0.091},
}


def to_creature_space(name, v, n, f):
    rig = RIG[name]
    if rig['kind'] == 'rigid':
        ax, ay, az = rig['anchor']
        return (v - np.array([ax, ay, az], np.float32)) / rig['r'], n, f
    z = v[:, 2]
    zc = z[f].mean(1)
    f = f[(zc >= rig['keep'][0]) & (zc <= rig['keep'][1])]
    nv = np.stack([(rig['front'] - z) / rig['r'], (v[:, 1] - rig['cy']) / rig['r'], v[:, 0] / rig['r']], 1)
    nn = np.stack([-n[:, 2], n[:, 1], n[:, 0]], 1)
    return nv.astype(np.float32), nn.astype(np.float32), f


def read_glb(path):
    data = open(path, 'rb').read()
    jl = struct.unpack_from('<I', data, 12)[0]
    js = json.loads(data[20:20 + jl])
    off = 20 + jl
    bl = struct.unpack_from('<I', data, off)[0]
    bin_ = data[off + 8: off + 8 + bl]

    def view(i):
        bv = js['bufferViews'][i]
        o = bv.get('byteOffset', 0)
        return bin_[o:o + bv['byteLength']]

    def accessor(i):
        a = js['accessors'][i]
        comp = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        raw = view(a['bufferView'])
        arr = np.frombuffer(raw, comp, count=a['count'] * n, offset=a.get('byteOffset', 0))
        return arr.reshape(a['count'], n) if n > 1 else arr

    prim = js['meshes'][0]['primitives'][0]
    pos = accessor(prim['attributes']['POSITION']).astype(np.float64)
    uv = accessor(prim['attributes']['TEXCOORD_0']).astype(np.float64)
    idx = accessor(prim['indices']).astype(np.int64).reshape(-1, 3)
    mat = js['materials'][prim.get('material', 0)]
    pbr = mat['pbrMetallicRoughness']

    def image(tex_ref):
        img = js['images'][js['textures'][tex_ref['index']]['source']]
        return Image.open(io.BytesIO(view(img['bufferView'])))

    imgs = {'base': image(pbr['baseColorTexture']), 'normal': image(mat['normalTexture']),
            'mr': image(pbr['metallicRoughnessTexture'])}
    return pos, uv, idx, imgs


def decimate(pos, uv, idx, target):
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(vertex_matrix=pos, face_matrix=idx, v_tex_coords_matrix=uv))
    ms.compute_texcoord_transfer_vertex_to_wedge()
    ms.meshing_remove_duplicate_vertices()
    ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=target, qualitythr=0.4,
                                                              preserveboundary=True, optimalplacement=True)
    m = ms.current_mesh()
    v = m.vertex_matrix()
    f = m.face_matrix()
    wtc = m.wedge_tex_coord_matrix().reshape(-1, 3, 2)
    # split vertices per unique (vertex, uv) pair
    key = np.concatenate([f.reshape(-1, 1).astype(np.float64), np.round(wtc.reshape(-1, 2), 6)], 1)
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    nv = v[uniq[:, 0].astype(np.int64)]
    nuv = uniq[:, 1:]
    nf = inv.reshape(-1, 3)
    # smooth normals from the welded topology, copied to split vertices
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    vn = np.zeros_like(v)
    for k in range(3):
        np.add.at(vn, f[:, k], fn)
    vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12
    nn = vn[uniq[:, 0].astype(np.int64)]
    return nv.astype(np.float32), nuv.astype(np.float32), nn.astype(np.float32), nf.astype(np.uint32)


def creature_normals(name, n):
    """Source-space normals -> creature space (same axis swap as to_creature_space)."""
    if RIG[name]['kind'] == 'rigid':
        return n
    return np.stack([-n[..., 2], n[..., 1], n[..., 0]], -1)


def bake_maps(name, pos, idx, v, t, f):
    """Bake the hi-poly onto the decimated mesh's UV atlas.
    Returns (object-space normal image in creature space, AO [0..1] image, thinness [0..1] image), all BAKE^2,
    oriented like the glTF textures (row 0 = v 0)."""
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(vertex_matrix=pos, face_matrix=idx))
    ms.meshing_remove_duplicate_vertices()
    ms.compute_normal_per_vertex()
    ms.compute_scalar_ambient_occlusion(rays=AO_RAYS)
    ao = ms.current_mesh().vertex_scalar_array().copy()
    ms.compute_scalar_by_shape_diameter_function_per_vertex(rays=48, cone_amplitude=90)
    sdf = ms.current_mesh().vertex_scalar_array().copy()
    hi = ms.current_mesh()
    hv, hf, hn = hi.vertex_matrix(), hi.face_matrix(), hi.vertex_normal_matrix()
    ao = np.clip(ao / 16.0, 0, 1)                                    # fraction of the hemisphere that sees open water
    sdf = np.where(np.isfinite(sdf), sdf, 10.0) / RIG[name]['r']     # local thickness in body radii (no hit = open = thick)
    thin = np.clip(1 - (sdf - 0.06) / 0.5, 0, 1) ** 1.5
    col = np.stack([ao, thin, np.zeros_like(ao), np.ones_like(ao)], 1)
    ms2 = pymeshlab.MeshSet()
    ms2.add_mesh(pymeshlab.Mesh(vertex_matrix=hv, face_matrix=hf, v_normals_matrix=hn, v_color_matrix=col))
    ms2.add_mesh(pymeshlab.Mesh(vertex_matrix=v.astype(np.float64), face_matrix=f.astype(np.int32),
                                w_tex_coords_matrix=t[f.reshape(-1)].astype(np.float64)))
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            for key, attr in (('nrm', 'Vertex Normal'), ('col', 'Vertex Color')):
                ms2.transfer_attributes_to_texture_per_vertex(sourcemesh=0, targetmesh=1, attributeenum=attr, textname=key + '.png',
                                                              textw=BAKE, texth=BAKE, overwrite=False, pullpush=True,
                                                              upperbound=pymeshlab.PercentageValue(2))
            ms2.set_current_mesh(1)
            ms2.save_current_mesh(os.path.join(tmp, 'lo.obj'))
            print('  baked', sorted(os.listdir(tmp)), flush=True)
            for key in ('nrm', 'col'):
                out[key] = np.asarray(Image.open(os.path.join(tmp, key + '.png')).convert('RGB'))[::-1].astype(np.float32) / 255
        finally:
            os.chdir(cwd)
    nrm = creature_normals(name, out['nrm'] * 2 - 1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-6
    nimg = Image.fromarray(np.clip((nrm * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8))
    return nimg, out['col'][..., 0], out['col'][..., 1]


def find_eyes(name, pos, uv, idx, base):
    """Eye centres from the painted red irises (head only), in creature space."""
    if name != 'head':
        return None
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    a = np.asarray(base.convert('RGB')).astype(np.float32) / 255
    h = a.shape[0]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = np.clip((r - np.maximum(g, b) - 0.18) * 3.5, 0, 1) * np.clip((r - 0.35) * 3, 0, 1)
    m = red[np.clip((uv[:, 1] * h).astype(int), 0, h - 1), np.clip((uv[:, 0] * h).astype(int), 0, h - 1)] > 0.3
    e = np.concatenate([idx[:, [0, 1]], idx[:, [1, 2]], idx[:, [2, 0]]])
    e = e[m[e[:, 0]] & m[e[:, 1]]]
    sel = np.where(m)[0]
    lut = np.full(len(pos), -1)
    lut[sel] = np.arange(len(sel))
    n, lab = connected_components(coo_matrix((np.ones(len(e)), (lut[e[:, 0]], lut[e[:, 1]])), shape=(len(sel), len(sel))))
    # outward normals of the hi-poly at those vertices
    fn = np.cross(pos[idx[:, 1]] - pos[idx[:, 0]], pos[idx[:, 2]] - pos[idx[:, 0]])
    vn = np.zeros_like(pos)
    for k in range(3):
        np.add.at(vn, idx[:, k], fn)
    rig = RIG[name]
    eyes = []
    for k in range(n):
        ids = sel[lab == k]
        if len(ids) < 200:
            continue
        c = (pos[ids].mean(0) - np.array(rig['anchor'])) / rig['r']
        nn = vn[ids].sum(0)
        nn /= np.linalg.norm(nn) + 1e-9
        rad = float(np.linalg.norm((pos[ids] - pos[ids].mean(0)) / rig['r'], axis=1).max())
        eyes.append({'c': c.round(4).tolist(), 'n': nn.round(4).tolist(), 'r': round(rad, 4)})
    # merge painted islands of the same eye (one per side)
    out = []
    for side in (-1, 1):
        g_ = [e_ for e_ in eyes if np.sign(e_['c'][2]) == side]
        if not g_:
            continue
        w = np.array([e_['r'] for e_ in g_])
        c = np.average([e_['c'] for e_ in g_], 0, w)
        nn = np.average([e_['n'] for e_ in g_], 0, w)
        nn /= np.linalg.norm(nn)
        out.append({'c': c.round(4).tolist(), 'n': nn.round(4).tolist(), 'r': round(float(max(w)), 4)})
    return out


def emissive_from_base(base):
    """Cyan cracks: saturated, blue-green dominant pixels -> glow map."""
    a = np.asarray(base.convert('RGB').resize((1024, 1024), Image.LANCZOS)).astype(np.float32) / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    cyan = np.clip((np.minimum(g, b) - r - 0.08) * 4.0, 0, 1) * np.clip((np.maximum(g, b) - 0.25) * 3, 0, 1)
    red = np.clip((r - np.maximum(g, b) - 0.18) * 3.5, 0, 1) * np.clip((r - 0.35) * 3, 0, 1)
    em = np.stack([cyan * 0.25 + red * 1.0, cyan * 0.96 + red * 0.25, cyan * 1.0 + red * 0.08], -1)
    return Image.fromarray((np.clip(em, 0, 1) * 255).astype(np.uint8))


# abyssal gradient map: luminance -> colour (black, deep navy, dark teal-slate, cold grey-green)
GRADE = [(0.00, (2, 4, 8)), (0.05, (6, 12, 21)), (0.12, (12, 26, 40)), (0.22, (24, 46, 58)),
         (0.36, (48, 72, 80)), (0.55, (96, 116, 118)), (1.00, (170, 188, 186))]
# every part is matched to the same tonal range so the head is not lighter than the body
TONE_SRC_PCT = [1, 10, 50, 90, 99]
TONE_DST = [0.0, 0.03, 0.09, 0.22, 0.40]


def grade_base(base):
    a = np.asarray(base.convert('RGB')).astype(np.float32) / 255
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    src = np.percentile(lum[lum > 0.01], TONE_SRC_PCT)
    t = np.interp(lum, src, TONE_DST)
    xs = [g[0] for g in GRADE]
    col = np.stack([np.interp(t, xs, [g[1][c] / 255 for g in GRADE]) for c in range(3)], -1)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    glow = np.clip((np.minimum(g, b) - r - 0.08) * 4.0, 0, 1) + np.clip((r - np.maximum(g, b) - 0.18) * 3.5, 0, 1)
    col = col * (1 - glow[..., None] * 0.8) + a * glow[..., None] * 0.8  # keep painted veins and eyes
    return Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8))


def jpg(img, size, q=88):
    b = io.BytesIO()
    img.convert('RGB').resize((size, size), Image.LANCZOS).save(b, 'JPEG', quality=q, subsampling=0 if q > 90 else 2)
    return b.getvalue()


def write_glb(path, v, uv, n, f, tex):
    blobs, views, accs = [], [], []

    def add(arr, target, comp, typ, minmax=False):
        raw = arr.tobytes()
        off = sum(len(x) for x in blobs)
        blobs.append(raw + b'\0' * (-len(raw) % 4))
        views.append({'buffer': 0, 'byteOffset': off, 'byteLength': len(raw), **({'target': target} if target else {})})
        a = {'bufferView': len(views) - 1, 'componentType': comp, 'count': len(arr), 'type': typ}
        if minmax:
            a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
        accs.append(a)
        return len(accs) - 1

    ip = add(v, 34962, 5126, 'VEC3', True)
    inn = add(n, 34962, 5126, 'VEC3')
    iu = add(uv, 34962, 5126, 'VEC2')
    ii = add(f.reshape(-1), 34963, 5125, 'SCALAR')
    images = []
    for name in ['base', 'normal', 'mr', 'emissive']:
        raw = tex[name]
        off = sum(len(x) for x in blobs)
        blobs.append(raw + b'\0' * (-len(raw) % 4))
        views.append({'buffer': 0, 'byteOffset': off, 'byteLength': len(raw)})
        images.append({'bufferView': len(views) - 1, 'mimeType': 'image/jpeg', 'name': name})
    js = {
        'asset': {'version': '2.0', 'generator': 'descent build_leviathan.py'},
        'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0, 'name': os.path.basename(path)[:-4]}],
        'meshes': [{'primitives': [{'attributes': {'POSITION': ip, 'NORMAL': inn, 'TEXCOORD_0': iu}, 'indices': ii, 'material': 0}]}],
        'materials': [{'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}, 'metallicRoughnessTexture': {'index': 2}},
                       'normalTexture': {'index': 1}, 'emissiveTexture': {'index': 3}, 'emissiveFactor': [1, 1, 1]}],
        'textures': [{'source': i, 'sampler': 0} for i in range(4)],
        'samplers': [{'magFilter': 9729, 'minFilter': 9987}],
        'images': images, 'accessors': accs, 'bufferViews': views,
        'buffers': [{'byteLength': sum(len(x) for x in blobs)}],
    }
    jb = json.dumps(js, separators=(',', ':')).encode()
    jb += b' ' * (-len(jb) % 4)
    bb = b''.join(blobs)
    with open(path, 'wb') as fh:
        fh.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(jb) + 8 + len(bb)))
        fh.write(struct.pack('<II', len(jb), 0x4E4F534A) + jb)
        fh.write(struct.pack('<II', len(bb), 0x004E4942) + bb)


def write_web(name, v, uv, n, f, tex, extra=None):
    """Artifact-friendly copy: compact JSON geometry (base64 typed arrays) + one JPG per map."""
    import base64
    used = np.unique(f)
    remap = np.full(len(v), -1, np.int64)
    remap[used] = np.arange(len(used))
    v, uv, n, f = v[used], uv[used], n[used], remap[f]
    b64 = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
    geo = {'count': int(len(v)), 'pos': b64(v.astype(np.float32)), 'nrm': b64(np.round(n * 127).astype(np.int8)),
           'uv': b64(np.round(np.clip(uv, 0, 1) * 65535).astype(np.uint16)),
           'idx': b64(f.astype(np.uint16 if len(v) < 65536 else np.uint32).reshape(-1)),
           'idx32': bool(len(v) >= 65536),
           'min': v.min(0).round(4).tolist(), 'max': v.max(0).round(4).tolist(), **(extra or {})}
    with open(os.path.join(OUT, f'lev_{name}.json'), 'w') as fh:
        json.dump(geo, fh, separators=(',', ':'))
    for k, raw in tex.items():
        with open(os.path.join(OUT, f'lev_{name}_{k}.jpg'), 'wb') as fh:
            fh.write(raw)


def main():
    only = sys.argv[1:]
    for name, src, target in PARTS:
        if only and name not in only:
            continue
        pos, uv, idx, imgs = read_glb(os.path.join(SRC, src))
        print(name, 'src', len(pos), 'verts', len(idx), 'tris', {k: v.size for k, v in imgs.items()}, flush=True)
        v, t, n, f = decimate(pos, uv, idx, target)
        nimg, ao, thin = bake_maps(name, pos, idx, v, t, f)
        eyes = find_eyes(name, pos, uv, idx, imgs['base'])
        v, n, f = to_creature_space(name, v, n, f)
        rough = np.asarray(imgs['mr'].convert('RGB').resize((BAKE, BAKE), Image.LANCZOS))[..., 1]
        mr = Image.fromarray(np.stack([np.clip(ao * 255 + 0.5, 0, 255).astype(np.uint8), rough,
                                       np.clip(thin * 255 + 0.5, 0, 255).astype(np.uint8)], -1))
        tex = {'base': jpg(grade_base(imgs['base']), TEX), 'normal': jpg(nimg, BAKE, 95), 'mr': jpg(mr, BAKE, 92),
               'emissive': jpg(emissive_from_base(imgs['base']), 1024)}
        extra = {'nrm': 'object', 'mr': 'ao-rough-thin', **({'eyes': eyes} if eyes else {})}
        write_web(name, v, t, n, f, tex, extra)
        print(' eyes', eyes, flush=True) if eyes else None
        print(' ->', name, len(v), 'verts', len(f), 'tris', flush=True)


if __name__ == '__main__':
    main()
