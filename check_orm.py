import cv2
import numpy as np
import glob

files = glob.glob('slot_engine/static/assets/pbr/*_orm.png')
for f in files:
    img = cv2.imread(f, cv2.IMREAD_UNCHANGED)
    if img is not None:
        print(f"{f}: R mean = {np.mean(img[:,:,2])}") # cv2 is BGR! so R is index 2
