from PIL import Image
import numpy as np
img = Image.open('slot_engine/static/snapshots/engine_m1_verified.png')
img = img.convert('RGB')
arr = np.array(img)
h, w, c = arr.shape
center = arr[h//3:2*h//3, w//3:2*w//3]
std = center.std(axis=(0,1))
print("Center std color:", std)
unique = np.unique(center.reshape(-1, 3), axis=0)
print("Num unique colors:", len(unique))
