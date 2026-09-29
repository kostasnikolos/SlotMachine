import re

with open('slot_engine/static/js/monolithic_frame.js', 'r') as f:
    code = f.read()

# Fix texture repeat to 1x1 to stop bubble wrap
code = code.replace('tex.repeat.set(4, 4);', 'tex.repeat.set(1, 1);')

# Add normalScale to reduce extreme bumpiness
code = code.replace('normalMap: basaltNormal,', 'normalMap: basaltNormal,\n            normalScale: new THREE.Vector2(0.3, 0.3),')
code = code.replace('normalMap: steelNormal,', 'normalMap: steelNormal,\n            normalScale: new THREE.Vector2(0.5, 0.5),')

# Make the Barometer shader emissive and purple
code = code.replace('const fluidGeo = new THREE.CylinderGeometry(0.5, 0.5, fillHeight, 32);', '''
        const fluidGeo = new THREE.CylinderGeometry(0.5, 0.5, fillHeight, 32);
        this.plasmaMaterial = new THREE.MeshStandardMaterial({
            color: 0x8800ff,
            emissive: 0xaa00ff,
            emissiveIntensity: 3.0
        });
''')

with open('slot_engine/static/js/monolithic_frame.js', 'w') as f:
    f.write(code)
