import re

with open('slot_engine/static/js/WebGLGameEngine.js', 'r') as f:
    code = f.read()

# I added this block:
'''
        const keyMap = {
            'HIGH_LEVIATHAN': 'sym_high_leviathan',
            'HIGH_ANGLER': 'sym_high_angler',
            'HIGH_VIPER': 'sym_high_viper',
            'HIGH_SQUID': 'sym_high_squid',
            'MID_HELMET': 'sym_mid_helmet',
            'MID_COMPASS': 'sym_mid_compass',
            'WILD_MAW': 'sym_wild_maw',
            'DEAD_SEDIMENT': 'sym_dead_sediment',
            'LOW_10': 'rune_10',
            'LOW_J': 'rune_j',
            'LOW_Q': 'rune_q',
            'LOW_K': 'rune_k',
            'LOW_A': 'rune_a'
        };
        console.log("symbolKey:", symbolKey, "mapped:", keyMap[symbolKey] || symbolKey, "hasMat:", !!this.materials[keyMap[symbolKey] || symbolKey]); const mappedKey = keyMap[symbolKey] || symbolKey;
        if (this.materials[mappedKey]) {
            this.planes[idx].material = this.materials[mappedKey];
            this.planes[idx].material.emissiveIntensity = 2.0;
        }
'''

# Let's replace the whole update loop mapping logic back to normal.
code = re.sub(
    r'const keyMap = \{[\s\S]*?this\.planes\[idx\]\.material\.emissiveIntensity = 2\.0;\s*\}',
    r'''
                    if (this.materials[symbolKey]) {
                        this.planes[idx].material = this.materials[symbolKey];
                        this.planes[idx].material.emissiveIntensity = 2.0;
                    }
    '''.strip(),
    code
)

with open('slot_engine/static/js/WebGLGameEngine.js', 'w') as f:
    f.write(code)
