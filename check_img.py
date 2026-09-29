from PIL import Image
img = Image.open('slot_engine/static/assets/pbr/sym_dead_sediment_albedo.png')
print(img.mode)
print(img.getextrema())
