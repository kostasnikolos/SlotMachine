with open('slot_engine/static/style.css', 'r') as f:
    css = f.read()

css = css.replace(
    'background: rgba(1, 4, 10, 0.65) !important;',
    'background: transparent !important;'
)

new_css = '''
.grid-wrapper {
  background: rgba(1, 4, 10, 0.65);
  border-radius: 10px;
  border: 2px solid rgba(0, 240, 255, 0.22);
  box-shadow: 0 0 35px rgba(0, 0, 0, 0.85) inset;
  padding: 8px;
}
'''
with open('slot_engine/static/style.css', 'a') as f:
    f.write(new_css)
