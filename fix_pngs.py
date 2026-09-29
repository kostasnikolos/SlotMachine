import cv2
import glob
import os

files = glob.glob('slot_engine/static/assets/pbr/*.png')
for f in files:
    img = cv2.imread(f, cv2.IMREAD_UNCHANGED)
    if img is not None:
        cv2.imwrite(f, img)
        print(f"Rewrote {f}")
    else:
        print(f"Failed to read {f}")
