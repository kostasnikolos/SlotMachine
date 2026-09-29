import cv2
import glob

files = glob.glob('slot_engine/static/assets/pbr/*_albedo.png')
for f in files:
    img = cv2.imread(f, cv2.IMREAD_UNCHANGED)
    if img.shape[2] == 4:
        print(f"{f}: RGBA, alpha mean = {img[:,:,3].mean()}")
    else:
        print(f"{f}: RGB")
