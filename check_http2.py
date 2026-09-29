import urllib.request

symbols = [
    'sym_high_leviathan', 'sym_high_squid', 'sym_high_angler', 'sym_high_viper',
    'sym_mid_helmet', 'sym_mid_compass', 'sym_wild_maw', 'sym_dead_sediment',
    'rune_10', 'rune_j', 'rune_q', 'rune_k', 'rune_a'
]

for s in symbols:
    for ext in ['_albedo.png', '_normal.png', '_orm.png', '_emissive.png']:
        url = f"http://localhost:8085/static/assets/pbr/{s}{ext}"
        try:
            urllib.request.urlopen(url)
        except Exception as e:
            print(f"{s}{ext}: ERROR {e}")
print("Done")
