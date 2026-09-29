from PIL import Image, ImageDraw

def create_layer(filename, color, text, width=512, height=512, has_alpha=True):
    img = Image.new("RGBA" if has_alpha else "RGB", (width, height), (0, 0, 0, 0) if has_alpha else color)
    draw = ImageDraw.Draw(img)
    if has_alpha:
        # Draw a shape to make it distinct
        draw.ellipse([50, 50, width-50, height-50], fill=color, outline="white", width=5)
    else:
        draw.rectangle([0, 0, width, height], fill=color)
    
    # Just save it
    img.save(filename)

# Background (Void) - Opaque dark purple void
create_layer("/Users/kosta/SlotMachine/slot_engine/static/textures/sym_wild_maw_bg.png", (40, 10, 60, 255), "Void", has_alpha=False)

# Midground (Teeth) - Transparent with Red/White teeth
create_layer("/Users/kosta/SlotMachine/slot_engine/static/textures/sym_wild_maw_mid.png", (200, 50, 50, 255), "Teeth", has_alpha=True)

# Foreground (Saliva) - Transparent with Blue bubbles
create_layer("/Users/kosta/SlotMachine/slot_engine/static/textures/sym_wild_maw_fg.png", (100, 200, 255, 128), "Saliva", has_alpha=True)

print("Created 3 mock parallax textures.")
