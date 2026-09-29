from PIL import Image, ImageDraw, ImageFilter
import os

PBR_DIR = "/Users/kosta/SlotMachine/slot_engine/static/assets/pbr"
OUT_DIR = "/Users/kosta/SlotMachine/slot_engine/static/textures"

def process_textures():
    # Load original textures
    albedo = Image.open(f"{PBR_DIR}/sym_wild_maw_albedo.png").convert("RGBA")
    normal = Image.open(f"{PBR_DIR}/sym_wild_maw_normal.png").convert("RGBA")
    orm = Image.open(f"{PBR_DIR}/sym_wild_maw_orm.png").convert("RGBA")
    emissive = Image.open(f"{PBR_DIR}/sym_wild_maw_emissive.png").convert("RGBA")
    
    width, height = albedo.size
    
    # --- Background (Void) ---
    # Blur and darken the albedo
    bg_albedo = albedo.copy()
    bg_albedo = bg_albedo.filter(ImageFilter.GaussianBlur(10))
    # Darken
    bg_albedo = bg_albedo.point(lambda p: p * 0.3)
    bg_albedo.save(f"{OUT_DIR}/maw_bg_albedo.png")
    
    # --- Midground (Teeth) ---
    # Circular alpha mask
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    # Draw a circle in the center for the teeth mask
    margin = int(width * 0.1)
    draw.ellipse((margin, margin, width-margin, height-margin), fill=255)
    
    # Soften the edges of the mask
    mask = mask.filter(ImageFilter.GaussianBlur(5))
    
    # Apply mask to midground textures
    mid_albedo = albedo.copy()
    mid_albedo.putalpha(mask)
    mid_albedo.save(f"{OUT_DIR}/maw_mid_albedo.png")
    
    mid_normal = normal.copy()
    mid_normal.putalpha(mask)
    mid_normal.save(f"{OUT_DIR}/maw_mid_normal.png")
    
    mid_orm = orm.copy()
    mid_orm.putalpha(mask)
    mid_orm.save(f"{OUT_DIR}/maw_mid_orm.png")
    
    mid_emissive = emissive.copy()
    mid_emissive.putalpha(mask)
    mid_emissive.save(f"{OUT_DIR}/maw_mid_emissive.png")
    
    # --- Foreground (Saliva/Bubbles) ---
    # Draw saliva directly in the center to overlay the mouth
    fg_albedo = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    fg_draw = ImageDraw.Draw(fg_albedo)
    
    # Saliva drips right in the middle
    center_x = width // 2
    center_y = height // 2
    
    # Big central bubble/drip
    fg_draw.ellipse((center_x - 100, center_y - 50, center_x + 100, center_y + 100), fill=(220, 240, 255, 160))
    # Another drip
    fg_draw.ellipse((center_x - 30, center_y + 80, center_x + 30, center_y + 180), fill=(220, 240, 255, 180))
    
    fg_albedo = fg_albedo.filter(ImageFilter.GaussianBlur(3))
    fg_albedo.save(f"{OUT_DIR}/maw_fg_albedo.png")
    
    # Foreground ORM: Non-metal (B=0) because metal is black without env map, low roughness (G=25), AO (R=255)
    fg_orm = Image.new("RGBA", (width, height), (255, 25, 0, 255))
    fg_orm.putalpha(mask) # Only saliva where the mouth is
    fg_orm.save(f"{OUT_DIR}/maw_fg_orm.png")

if __name__ == "__main__":
    process_textures()
    print("Processed PBR textures.")
