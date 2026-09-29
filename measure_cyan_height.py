import cv2
import numpy as np

img = cv2.imread('/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a/.user_uploaded/media_1790696675849.png')
lower_cyan = np.array([200, 200, 0])
upper_cyan = np.array([255, 255, 50])
mask = cv2.inRange(img, lower_cyan, upper_cyan)
y_coords, x_coords = np.where(mask > 0)
print(f"Cyan Box: X({np.min(x_coords)}-{np.max(x_coords)}), Y({np.min(y_coords)}-{np.max(y_coords)})")
