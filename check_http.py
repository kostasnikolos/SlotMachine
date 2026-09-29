import urllib.request

symbols = [
    'sym_high_leviathan', 'sym_high_squid', 'sym_high_angler', 'sym_high_viper',
    'sym_mid_helmet', 'sym_mid_compass', 'sym_wild_maw', 'sym_dead_sediment',
    'rune_10', 'rune_j', 'rune_q', 'rune_k', 'rune_a'
]

for s in symbols:
    url = f"http://localhost:8085/static/assets/pbr/{s}_albedo.png"
    try:
        urllib.request.urlopen(url)
        print(f"{s}: 200 OK")
    except Exception as e:
        print(f"{s}: ERROR {e}")
