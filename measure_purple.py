import cv2
import numpy as np

img = cv2.imread('/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a/.user_uploaded/media_1790696675849.png')
# Find Purple (approximate)
lower_purple = np.array([100, 0, 100])
upper_purple = np.array([255, 100, 255])
mask = cv2.inRange(img, lower_purple, upper_purple)

y_coords, x_coords = np.where(mask > 0)
if len(x_coords) > 0:
    print(f"Purple Area: X({np.min(x_coords)}-{np.max(x_coords)}), Y({np.min(y_coords)}-{np.max(y_coords)})")
