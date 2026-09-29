import cv2
import numpy as np

img = cv2.imread('/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a/.user_uploaded/media_1790697780538.png')

mask = cv2.inRange(img, np.array([16,16,16]), np.array([18,18,18]))
y, x = np.where(mask > 0)
if len(x) > 0:
    print(f"X range: {np.min(x)} - {np.max(x)}")
    print(f"Y range: {np.min(y)} - {np.max(y)}")
