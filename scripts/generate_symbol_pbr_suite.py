import os
import cv2
import numpy as np

ASSETS_DIR = "/Users/kosta/SlotMachine/slot_engine/static/assets"
PBR_DIR = os.path.join(ASSETS_DIR, "pbr")
os.makedirs(PBR_DIR, exist_ok=True)

symbols = [
    "sym_high_angler.jpg", "sym_high_viper.jpg", "sym_high_squid.jpg", "sym_high_leviathan.jpg",
    "sym_mid_helmet.jpg", "sym_mid_compass.jpg",
    "sym_wild_maw.jpg", "sym_dead_sediment.jpg"
]

def generate_normal_map(img_gray):
    # Base structure (low freq)
    blur_large = cv2.GaussianBlur(img_gray, (9, 9), 0)
    # Detail structure (high freq)
    blur_small = cv2.GaussianBlur(img_gray, (3, 3), 0)
    
    # Compute Scharr derivatives for base
    scharr_x_base = cv2.Scharr(blur_large, cv2.CV_32F, 1, 0)
    scharr_y_base = cv2.Scharr(blur_large, cv2.CV_32F, 0, 1)
    
    # Compute Scharr derivatives for detail
    scharr_x_detail = cv2.Scharr(blur_small, cv2.CV_32F, 1, 0)
    scharr_y_detail = cv2.Scharr(blur_small, cv2.CV_32F, 0, 1)
    
    # Combine (we want some high freq scale/fang detail)
    scharr_x = scharr_x_base * 0.5 + scharr_x_detail * 0.5
    scharr_y = scharr_y_base * 0.5 + scharr_y_detail * 0.5
    
    # Normalize to -1 to 1 roughly, then add Z component
    strength = 1.5
    scharr_x = scharr_x / 255.0 * strength
    scharr_y = scharr_y / 255.0 * strength
    
    z = np.ones_like(scharr_x)
    
    # Combine into vectors
    normals = np.dstack((scharr_x, scharr_y, z))
    
    # Normalize vectors
    norms = np.linalg.norm(normals, axis=2, keepdims=True)
    normals = normals / norms
    
    # Map from [-1, 1] to [0, 255]
    normals_img = ((normals + 1.0) / 2.0 * 255.0).astype(np.uint8)
    # OpenCV uses BGR, but we want tangent space standard (RGB: X, Y, Z)
    # Red = X (Right), Green = Y (Up - we might need to invert), Blue = Z (Forward)
    # Let's write as RGB and then convert to BGR for saving
    r = normals_img[:, :, 0]
    g = 255 - normals_img[:, :, 1]  # Invert Y for standard OpenGL normal map
    b = normals_img[:, :, 2]
    normal_map_bgr = np.dstack((b, g, r))
    
    return normal_map_bgr

def generate_orm_map(img_gray, img_color):
    # Ambient Occlusion: Darken the crevices.
    # Inverse of blurred brightness
    blur = cv2.GaussianBlur(img_gray, (15, 15), 0)
    ao = cv2.normalize(blur, None, alpha=50, beta=255, norm_type=cv2.NORM_MINMAX)
    
    # Roughness: Darker areas (shadows/crevices) might be rough, brighter areas might be shiny
    # Let's just create a varied roughness based on intensity
    roughness = cv2.bitwise_not(img_gray)
    roughness = cv2.normalize(roughness, None, alpha=100, beta=250, norm_type=cv2.NORM_MINMAX)
    
    # Metalness: Almost zero for most things, maybe a bit on helmet/compass
    metalness = np.zeros_like(img_gray)
    
    # Combine into ORM (R=AO, G=Roughness, B=Metalness)
    # Since OpenCV uses BGR for saving, we'll pack it as B=Metalness, G=Roughness, R=AO
    orm_bgr = np.dstack((metalness, roughness, ao))
    return orm_bgr

def generate_emissive_map(img_gray, img_color):
    # Threshold to isolate the brightest parts (lures, photophores, runes)
    _, emissive_mask = cv2.threshold(img_gray, 200, 255, cv2.THRESH_BINARY)
    # Blur slightly for a glow effect
    emissive_mask = cv2.GaussianBlur(emissive_mask, (5, 5), 0)
    
    # Multiply the original color by the mask
    emissive_bgr = cv2.bitwise_and(img_color, img_color, mask=emissive_mask)
    return emissive_bgr

def process_symbol(filename):
    basename = os.path.splitext(filename)[0]
    filepath = os.path.join(ASSETS_DIR, filename)
    
    print(f"Processing {filename}...")
    
    img = cv2.imread(filepath)
    if img is None:
        print(f"Error reading {filepath}")
        return
        
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Albedo
    albedo_path = os.path.join(PBR_DIR, f"{basename}_albedo.png")
    cv2.imwrite(albedo_path, img)
    
    # 2. Normal Map
    normal_map = generate_normal_map(img_gray)
    normal_path = os.path.join(PBR_DIR, f"{basename}_normal.png")
    cv2.imwrite(normal_path, normal_map)
    
    # 3. ORM Map
    orm_map = generate_orm_map(img_gray, img)
    orm_path = os.path.join(PBR_DIR, f"{basename}_orm.png")
    cv2.imwrite(orm_path, orm_map)
    
    # 4. Emissive Map
    emissive_map = generate_emissive_map(img_gray, img)
    emissive_path = os.path.join(PBR_DIR, f"{basename}_emissive.png")
    cv2.imwrite(emissive_path, emissive_map)
    
    print(f"  Saved PBR maps for {basename}")

if __name__ == "__main__":
    for sym in symbols:
        process_symbol(sym)
    print("All PBR suites generated.")
