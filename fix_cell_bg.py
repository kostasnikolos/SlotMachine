import re

with open('slot_engine/static/style.css', 'r') as f:
    css = f.read()

# Change .symbol-cell background to transparent
css = css.replace(
    'background: linear-gradient(145deg, rgba(8, 16, 28, 0.94), rgba(2, 6, 12, 0.98));',
    'background: transparent;'
)

with open('slot_engine/static/style.css', 'w') as f:
    f.write(css)
