with open('slot_engine/static/style.css', 'r') as f:
    css = f.read()

css = css.replace(
    'padding: 8px;\n  background: transparent !important;\n  border: 2px solid rgba(0, 240, 255, 0.22);\n  border-radius: 10px;\n  box-shadow: 0 0 35px rgba(0, 0, 0, 0.85) inset;',
    'padding: 0;\n  background: transparent !important;\n  border: none;\n  box-shadow: none;'
)

with open('slot_engine/static/style.css', 'w') as f:
    f.write(css)
