import re

with open('slot_engine/config/weights.py', 'r') as f:
    code = f.read()

replacement_lvl3 = """    DepthLevel.LEVEL_3_ABYSS: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 0,
        SymbolType.LOW_Q: 0,
        SymbolType.LOW_K: 25,
        SymbolType.LOW_A: 25,
        SymbolType.MID_HELMET: 20,
        SymbolType.MID_COMPASS: 20,
        SymbolType.HIGH_VIPER: 12,
        SymbolType.HIGH_ANGLER: 8,
        SymbolType.HIGH_SQUID: 5,
        SymbolType.HIGH_LEVIATHAN: 2,
        SymbolType.WILD_MAW: 3,
        SymbolType.DEAD_SEDIMENT: 60,
    },"""

code = re.sub(r'    DepthLevel\.LEVEL_3_ABYSS: \{.*?\},\n', replacement_lvl3 + '\n', code, flags=re.DOTALL)

replacement_lvl4 = """    DepthLevel.LEVEL_4_HADAL: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 0,
        SymbolType.LOW_Q: 0,
        SymbolType.LOW_K: 0,
        SymbolType.LOW_A: 25,
        SymbolType.MID_HELMET: 22,
        SymbolType.MID_COMPASS: 20,
        SymbolType.HIGH_VIPER: 15,
        SymbolType.HIGH_ANGLER: 10,
        SymbolType.HIGH_SQUID: 6,
        SymbolType.HIGH_LEVIATHAN: 3,
        SymbolType.WILD_MAW: 3,
        SymbolType.DEAD_SEDIMENT: 80,
    },"""

code = re.sub(r'    DepthLevel\.LEVEL_4_HADAL: \{.*?\},\n', replacement_lvl4 + '\n', code, flags=re.DOTALL)

replacement_lvl5 = """    DepthLevel.LEVEL_5_CORE: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 0,
        SymbolType.LOW_Q: 0,
        SymbolType.LOW_K: 0,
        SymbolType.LOW_A: 0,
        SymbolType.MID_HELMET: 25,
        SymbolType.MID_COMPASS: 25,
        SymbolType.HIGH_VIPER: 20,
        SymbolType.HIGH_ANGLER: 12,
        SymbolType.HIGH_SQUID: 8,
        SymbolType.HIGH_LEVIATHAN: 4,
        SymbolType.WILD_MAW: 3,
        SymbolType.DEAD_SEDIMENT: 120,
    },"""

code = re.sub(r'    DepthLevel\.LEVEL_5_CORE: \{.*?\},\n', replacement_lvl5 + '\n', code, flags=re.DOTALL)

with open('slot_engine/config/weights.py', 'w') as f:
    f.write(code)
