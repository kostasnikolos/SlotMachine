import re

with open('slot_engine/config/weights.py', 'r') as f:
    code = f.read()

code = re.sub(r"SymbolType.DEAD_SEDIMENT: 60", "SymbolType.DEAD_SEDIMENT: 110", code)
code = re.sub(r"SymbolType.DEAD_SEDIMENT: 80", "SymbolType.DEAD_SEDIMENT: 150", code)
code = re.sub(r"SymbolType.DEAD_SEDIMENT: 120", "SymbolType.DEAD_SEDIMENT: 200", code)

with open('slot_engine/config/weights.py', 'w') as f:
    f.write(code)
