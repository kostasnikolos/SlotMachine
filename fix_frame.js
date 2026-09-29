const fs = require('fs');
let code = fs.readFileSync('slot_engine/static/js/monolithic_frame.js', 'utf8');

// Fix texture repeat to 1x1 to stop bubble wrap
code = code.replace(/tex\.repeat\.set\(4, 4\);/g, 'tex.repeat.set(1, 1);');

// Add normalScale to reduce extreme bumpiness
code = code.replace(/normalMap: basaltNormal,/g, 'normalMap: basaltNormal,\n            normalScale: new THREE.Vector2(0.3, 0.3),');
code = code.replace(/normalMap: steelNormal,/g, 'normalMap: steelNormal,\n            normalScale: new THREE.Vector2(0.5, 0.5),');

// Make the Barometer shader emissive and purple
code = code.replace(/const fluidGeo = new THREE\.CylinderGeometry\(0\.5, 0\.5, fillHeight, 32\);/g, `
        const fluidGeo = new THREE.CylinderGeometry(0.5, 0.5, fillHeight, 32);
        this.plasmaMaterial = new THREE.MeshStandardMaterial({
            color: 0x8800ff,
            emissive: 0xaa00ff,
            emissiveIntensity: 3.0
        });
`);

fs.writeFileSync('slot_engine/static/js/monolithic_frame.js', code);
